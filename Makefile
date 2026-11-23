IMAGE_NAME := linux-hil-val-suite:latest
REPORTS_DIR := $(CURDIR)/reports
LOGS_DIR := $(CURDIR)/logs

.PHONY: build-dut docker-build test test-sanity clean

## בניית מודול הקרנל, הדמון ואריזת initramfs.cpio.gz
build-dut:
	./dut/image_builder/build_rootfs.sh

## בניית תמונת ה-Docker
docker-build:
	docker build -f docker/Dockerfile -t $(IMAGE_NAME) .

## הרצת כל חבילת הטסטים בתוך Docker ושמירת דוחות ולוגים על המארח
test:
	mkdir -p $(REPORTS_DIR) $(LOGS_DIR)
	docker run --rm \
		-v $(REPORTS_DIR):/app/reports \
		-v $(LOGS_DIR):/app/logs \
		$(IMAGE_NAME)

## הרצת בדיקת Boot Sanity בלבד
test-sanity:
	mkdir -p $(REPORTS_DIR) $(LOGS_DIR)
	docker run --rm \
		-v $(REPORTS_DIR):/app/reports \
		-v $(LOGS_DIR):/app/logs \
		$(IMAGE_NAME) tests/test_01_boot_sanity.py

## ניקוי דוחות ולוגים מקומיים
clean:
	rm -rf $(REPORTS_DIR)/* $(LOGS_DIR)/*