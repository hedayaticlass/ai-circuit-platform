FROM python:3.12-slim

WORKDIR /app

# ngspice مورد نیاز PySpice است.
# نکته مهم: pyspice به دنبال libngspice.so (بدون عدد نسخه) می‌گردد.
# پکیج ngspice فقط باینری CLI را می‌دهد؛ پکیج libngspice0 فقط libngspice.so.0
# را می‌دهد (با عدد نسخه). فقط libngspice0-dev فایل بدون‌عدد (symlink) را
# فراهم می‌کند که PySpice به آن نیاز دارد.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ngspice \
        libngspice0-dev \
    && rm -rf /var/lib/apt/lists/*

# مطمئن می‌شویم لودر کتابخانه‌های دینامیک مسیر را می‌شناسد (در بعضی image
# های پایه لازم است صریحاً ldconfig اجرا شود)
RUN ldconfig

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
