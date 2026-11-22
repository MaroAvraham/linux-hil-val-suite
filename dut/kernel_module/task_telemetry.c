#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>
#include <linux/mutex.h>
#include "../include/telemetry_ioctl.h"

#define DEVICE_NAME "task_telemetry"
#define CLASS_NAME  "telemetry_cls"
#define MAX_THRESHOLD 10000

static dev_t dev_num;
static struct cdev telemetry_cdev;
static struct class *telemetry_class;
static struct device *telemetry_device;

static DEFINE_MUTEX(telemetry_lock);
static struct telemetry_stats g_stats = {
    .event_count = 0,
    .alert_threshold = 100,
    .alert_triggered = 0
};

/* --- Sysfs: קריאה וכתיבה של סף ההתראה דרך /sys/class/telemetry_cls/task_telemetry/threshold --- */
static ssize_t threshold_show(struct device *dev, struct device_attribute *attr, char *buf)
{
    uint32_t val;
    mutex_lock(&telemetry_lock);
    val = g_stats.alert_threshold;
    mutex_unlock(&telemetry_lock);
    return sysfs_emit(buf, "%u\n", val);
}

static ssize_t threshold_store(struct device *dev, struct device_attribute *attr, const char *buf, size_t count)
{
    uint32_t val;
    if (kstrtou32(buf, 10, &val) < 0 || val == 0 || val > MAX_THRESHOLD)
        return -EINVAL;

    mutex_lock(&telemetry_lock);
    g_stats.alert_threshold = val;
    g_stats.alert_triggered = (g_stats.event_count >= val) ? 1 : 0;
    mutex_unlock(&telemetry_lock);
    return count;
}
static DEVICE_ATTR_RW(threshold);

/* --- File Operations: פתיחה, קריאה ו-ioctl על /dev/task_telemetry --- */
static int telemetry_open(struct inode *inode, struct file *file)
{
    mutex_lock(&telemetry_lock);
    g_stats.event_count++;
    if (g_stats.event_count >= g_stats.alert_threshold)
        g_stats.alert_triggered = 1;
    mutex_unlock(&telemetry_lock);
    return 0;
}

static ssize_t telemetry_read(struct file *file, char __user *buf, size_t len, loff_t *offset)
{
    char msg[64];
    int msg_len;

    if (*offset > 0)
        return 0; /* EOF */

    mutex_lock(&telemetry_lock);
    msg_len = snprintf(msg, sizeof(msg), "events=%u threshold=%u alert=%u\n",
                       g_stats.event_count, g_stats.alert_threshold, g_stats.alert_triggered);
    mutex_unlock(&telemetry_lock);

    if (len < msg_len)
        return -EINVAL;
    if (copy_to_user(buf, msg, msg_len))
        return -EFAULT;

    *offset += msg_len;
    return msg_len;
}

static long telemetry_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct telemetry_stats local_stats;
    uint32_t new_thresh;

    switch (cmd) {
    case TELEMETRY_IOC_RESET:
        mutex_lock(&telemetry_lock);
        g_stats.event_count = 0;
        g_stats.alert_triggered = 0;
        mutex_unlock(&telemetry_lock);
        pr_info("task_telemetry: stats reset via ioctl\n");
        return 0;

    case TELEMETRY_IOC_GET_STATS:
        mutex_lock(&telemetry_lock);
        local_stats = g_stats;
        mutex_unlock(&telemetry_lock);
        if (copy_to_user((void __user *)arg, &local_stats, sizeof(local_stats)))
            return -EFAULT;
        return 0;

    case TELEMETRY_IOC_SET_THRESHOLD:
        if (copy_from_user(&new_thresh, (void __user *)arg, sizeof(new_thresh)))
            return -EFAULT;
        if (new_thresh == 0 || new_thresh > MAX_THRESHOLD)
            return -EINVAL;
        mutex_lock(&telemetry_lock);
        g_stats.alert_threshold = new_thresh;
        g_stats.alert_triggered = (g_stats.event_count >= new_thresh) ? 1 : 0;
        mutex_unlock(&telemetry_lock);
        return 0;

    default:
        return -ENOTTY; /* פקודת ioctl לא מוכרת */
    }
}

static const struct file_operations telemetry_fops = {
    .owner          = THIS_MODULE,
    .open           = telemetry_open,
    .read           = telemetry_read,
    .unlocked_ioctl = telemetry_ioctl,
};

/* --- אתחול וניקוי נקי של המודול --- */
static int __init telemetry_init(void)
{
    int ret;

    ret = alloc_chrdev_region(&dev_num, 0, 1, DEVICE_NAME);
    if (ret < 0)
        return ret;

    cdev_init(&telemetry_cdev, &telemetry_fops);
    ret = cdev_add(&telemetry_cdev, dev_num, 1);
    if (ret < 0)
        goto err_cdev;

    /* הערה: בקרנל 6.4+ class_create מקבלת פרמטר אחד. לקרנל 5.15 יש להוסיף THIS_MODULE כפרמטר ראשון */
    telemetry_class = class_create(CLASS_NAME);
    if (IS_ERR(telemetry_class)) {
        ret = PTR_ERR(telemetry_class);
        goto err_class;
    }

    telemetry_device = device_create(telemetry_class, NULL, dev_num, NULL, DEVICE_NAME);
    if (IS_ERR(telemetry_device)) {
        ret = PTR_ERR(telemetry_device);
        goto err_device;
    }

    ret = device_create_file(telemetry_device, &dev_attr_threshold);
    if (ret < 0)
        goto err_sysfs;

    pr_info("task_telemetry: module loaded (major=%d)\n", MAJOR(dev_num));
    return 0;

err_sysfs:
    device_destroy(telemetry_class, dev_num);
err_device:
    class_destroy(telemetry_class);
err_class:
    cdev_del(&telemetry_cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
    return ret;
}

static void __exit telemetry_exit(void)
{
    device_remove_file(telemetry_device, &dev_attr_threshold);
    device_destroy(telemetry_class, dev_num);
    class_destroy(telemetry_class);
    cdev_del(&telemetry_cdev);
    unregister_chrdev_region(dev_num, 1);
    pr_info("task_telemetry: module unloaded cleanly\n");
}

module_init(telemetry_init);
module_exit(telemetry_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Avraham Maro");
MODULE_DESCRIPTION("Task Telemetry Character Driver for HIL Validation");