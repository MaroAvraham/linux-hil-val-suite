IMAGE_NAME  := linux-hil-val-suite:latest
REPORTS_DIR := $(CURDIR)/reports
LOGS_DIR    := $(CURDIR)/logs
RELEASE_URL := https://github.com/MaroAvraham/linux-hil-val-suite/releases/download/v1.0-prebuilt-dut

.PHONY: fetch-artifacts build-dut docker-build test test-sanity clean

## מוריד ארטיפקטי DUT מה-Release רק אם הם חסרים מקומית (מאפשר Quick Start במחשב נקי)
fetch-artifacts:
	@mkdir -p build
	@if [ ! -f build/bzImage ]; then \
		echo "Downloading prebuilt bzImage..."; \
		curl -fSL -o build/bzImage $(RELEASE_URL)/bzImage; \
	fi
	@if [ ! -f build/initramfs.cpio.gz ]; then \
		echo "Downloading prebuilt initramfs.cpio.gz..."; \
		curl -fSL -o build/initramfs.cpio.gz $(RELEASE_URL)/initramfs.cpio.gz; \
	fi

## בנייה מקומית של מודול הקרנל, הדמון ואריזת initramfs.cpio.gz
build-dut:
	./dut/image_builder/build_rootfs.sh

## בניית תמונת ה-Docker (מוודא קודם שהארטיפקטים קיימים)
docker-build: fetch-artifacts
	docker build -f docker/Dockerfile -t $(IMAGE_NAME) .

## הרצת כל חבילת הטסטים בתוך Docker ושמירת דוחות ולוגים על המארח
test:
	mkdir -p $(REPORTS_DIR)$(LOGS_DIR)
	docker run --rm \
		-v $(REPORTS_DIR):/app/reports \
		-v $(LOGS_DIR):/app/logs \
		$(IMAGE_NAME)

## הרצת בדיקת Boot Sanity בלבד
test-sanity:
	mkdir -p $(REPORTS_DIR)$(LOGS_DIR)
	docker run --rm \
		-v $(REPORTS_DIR):/app/reports \
		-v $(LOGS_DIR):/app/logs \
		$(IMAGE_NAME) -m sanity

## ניקוי דוחות ולוגים מקומיים
clean:
	rm -rf $(REPORTS_DIR)/*$(LOGS_DIR)/*