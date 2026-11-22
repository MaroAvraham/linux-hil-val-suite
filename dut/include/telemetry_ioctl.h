#ifndef TELEMETRY_IOCTL_H
#define TELEMETRY_IOCTL_H

#ifdef __KERNEL__
#include <linux/ioctl.h>
#include <linux/types.h>
#else
#include <sys/ioctl.h>
#include <stdint.h>
#endif

/* מספר קסם ייחודי שמזהה את הדרייבר שלנו */
#define TELEMETRY_IOC_MAGIC 'T'

/* מבנה הנתונים שעובר בין הקרנל למשתמש */
struct telemetry_stats {
    uint32_t event_count;
    uint32_t alert_threshold;
    uint32_t alert_triggered;
};

/* פקודות ioctl: איפוס, שליפת נתונים, והגדרת סף התראה */
#define TELEMETRY_IOC_RESET         _IO(TELEMETRY_IOC_MAGIC, 1)
#define TELEMETRY_IOC_GET_STATS     _IOR(TELEMETRY_IOC_MAGIC, 2, struct telemetry_stats)
#define TELEMETRY_IOC_SET_THRESHOLD _IOW(TELEMETRY_IOC_MAGIC, 3, uint32_t)

#endif /* TELEMETRY_IOCTL_H */