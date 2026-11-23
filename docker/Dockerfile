FROM ubuntu:22.04

# מונע משאלות אינטראקטיביות בזמן התקנת חבילות (כמו בחירת אזור זמן)
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. התקנת QEMU ו-Python בלבד + ניקוי מטמון apt לשמירה על תמונה רזה
RUN apt-get update && apt-get install -y --no-install-recommends \
    qemu-system-x86 \
    qemu-utils \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. התקנת תלויות Python לפני העתקת הקוד (מנצל Docker Layer Caching)
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. העתקת ארטיפקטי ה-DUT משלב 1 ו-2
COPY build/bzImage build/bzImage
COPY build/initramfs.cpio.gz build/initramfs.cpio.gz

# 4. העתקת קוד התשתית, הטסטים וההגדרות
COPY pytest.ini .
COPY harness/ harness/
COPY tests/ tests/
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh \
    && mkdir -p /app/reports /app/logs

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]