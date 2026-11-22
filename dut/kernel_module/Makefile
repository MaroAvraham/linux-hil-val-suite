obj-m += task_telemetry.o
ccflags-y := -Wall -Werror

# נתיב ברירת מחדל לעץ הקרנל משלב 1 (ניתן לדרוס מבחוץ)
KDIR ?= $(CURDIR)/../../src/linux

all:
	$(MAKE) -C $(KDIR) M=$(CURDIR) modules

clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) clean