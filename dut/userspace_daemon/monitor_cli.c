#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/ioctl.h>
#include "../include/telemetry_ioctl.h"

#define DEV_PATH "/dev/task_telemetry"

static volatile sig_atomic_t keep_running = 1;

static void handle_sigterm(int sig)
{
    (void)sig;
    keep_running = 0;
}

static int print_stats(int fd)
{
    struct telemetry_stats stats;
    if (ioctl(fd, TELEMETRY_IOC_GET_STATS, &stats) < 0) {
        perror("ioctl GET_STATS failed");
        return -1;
    }
    printf("events=%u threshold=%u alert=%u\n",
           stats.event_count, stats.alert_threshold, stats.alert_triggered);
    fflush(stdout);
    return 0;
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s [--stats | --reset | --threshold <val> | --daemon]\n", argv[0]);
        return 1;
    }

    int fd = open(DEV_PATH, O_RDWR);
    if (fd < 0) {
        perror("Failed to open " DEV_PATH);
        return 1;
    }

    int ret = 0;

    if (strcmp(argv[1], "--stats") == 0) {
        ret = print_stats(fd);
    } else if (strcmp(argv[1], "--reset") == 0) {
        if (ioctl(fd, TELEMETRY_IOC_RESET) < 0) {
            perror("ioctl RESET failed");
            ret = 1;
        } else {
            printf("Stats reset successfully.\n");
        }
    } else if (strcmp(argv[1], "--threshold") == 0 && argc == 3) {
        uint32_t val = (uint32_t)strtoul(argv[2], NULL, 10);
        if (ioctl(fd, TELEMETRY_IOC_SET_THRESHOLD, &val) < 0) {
            perror("ioctl SET_THRESHOLD failed");
            ret = 1;
        } else {
            printf("Threshold updated to %u.\n", val);
        }
    } else if (strcmp(argv[1], "--daemon") == 0) {
        signal(SIGTERM, handle_sigterm);
        signal(SIGINT, handle_sigterm);
        printf("monitor_cli daemon started (PID=%d)\n", getpid());
        fflush(stdout);
        while (keep_running) {
            print_stats(fd);
            sleep(2);
        }
        printf("monitor_cli daemon exiting cleanly.\n");
    } else {
        fprintf(stderr, "Invalid arguments.\n");
        ret = 1;
    }

    close(fd);
    return ret < 0 ? 1 : ret;
}