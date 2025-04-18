import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Sayfa başlığı ve ikonu
st.set_page_config(page_title="Excel Yönetimi ve Dönüştürme", page_icon="📊", layout="wide")

st.markdown("<h1 style='text-align: center;'>Excel Yönetimi ve Dönüştürme</h1>", unsafe_allow_html=True)

# Klasör ayarları
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Kullanıcı seçimi: Yeni dosya yükle veya mevcut bir dosyayı seç
option = st.radio(
    "Seçim Yapın:",
    ("Yeni Excel Dosyası Yükle", "Kayıtlı Bir Dosyayı Seç")
)

uploaded_file = None
selected_file = None

if option == "Yeni Excel Dosyası Yükle":
    # Tarih seçimi (başlangıçta "Lütfen tarih seçin" yazısı gösterilir)
    selected_date = st.date_input("Lütfen tarih seçin", value=None)

    # Tarih seçilmediyse uyarı göster ve dosya yüklemeyi engelle
    if selected_date is None:
        st.warning("Lütfen bir tarih seçin.")
    else:
        # Tarihi Türkçe olarak formatla
        turkish_months = [
            "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
            "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
        ]
        formatted_date = f"{selected_date.day} {turkish_months[selected_date.month - 1]} {selected_date.year}"
        st.write(f"Seçilen Tarih: {formatted_date}")

        uploaded_file = st.file_uploader("Bir Excel dosyası yükleyin (.xlsx veya .xls)", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            # Dosya adını sadece tarihe göre oluştur
            date_str = selected_date.strftime("%Y-%m-%d")
            file_name = f"{date_str}.xlsx"  # Sadece tarih bilgisi ile dosya adı oluştur
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            
            # Dosya daha önce yüklenmiş mi kontrol et
            if os.path.exists(file_path):
                st.warning(f"Bu dosya zaten sistemde bulunuyor: {file_name}")
            else:
                # Dosyayı klasöre kaydet
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Dosyanız başarıyla eklenmiştir. Dosya Adı: {file_name}")

elif option == "Kayıtlı Bir Dosyayı Seç":
    # Kayıtlı dosyaları listele (sadece belirli tarih formatına sahip dosyalar)
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith((".xlsx", ".xls"))]
    
    # Tarih formatına uygun dosyaları filtrele
    def is_valid_date_format(filename):
        try:
            # Dosya adından tarih kısmını al (örneğin: "2023-10-05.xlsx" -> "2023-10-05")
            date_part = filename.split(".")[0]
            datetime.strptime(date_part, "%Y-%m-%d")  # Tarih formatını kontrol et
            return True
        except ValueError:
            return False

    # Sadece tarih formatına uygun dosyaları listele
    valid_files = [f for f in files if is_valid_date_format(f)]
    
    if valid_files:
        # "Lütfen bir dosya seçin" seçeneği ekle
        files_with_prompt = ["Lütfen bir dosya seçin"] + valid_files
        selected_file = st.selectbox("Bir dosya seçin:", files_with_prompt)
        
        # Eğer kullanıcı "Lütfen bir dosya seçin" dışında bir dosya seçerse
        if selected_file != "Lütfen bir dosya seçin":
            st.info(f"Seçilen dosya işleniyor: {selected_file}")
            file_path = os.path.join(UPLOAD_FOLDER, selected_file)
            
            # Excel dosyasını oku
            df = pd.read_excel(file_path)

            # Sürücü kolonu boşsa "Dağıtım Aracı" olarak doldur
            df['Sürücü'] = df['Sürücü'].fillna("Dağıtım Aracı")

            # Diğer dönüştürme işlemleri
            if 'Hız (km/sa)' in df.columns:
                df['Hız (km/sa)'] = df['Hız (km/sa)'].astype(str).str.replace(',', '').astype(float)
            if 'Yol (km)' in df.columns:
                df['Yol (km)'] = df['Yol (km)'].astype(str).str.replace(',', '').astype(float)

            # Dönüştürülmüş veriler için DataFrame
            new_df = pd.DataFrame(columns=[
                "PLAKA", "SÜRÜCÜ", "TARİH", "KONTAK AÇILMA", "İL", "AKŞAM KONAKLAMA İL",
                "VARIŞ SAATİ EVE YA DA OTELE", "GÜNE BAŞLAMA KM", "GÜN BİTİRME KM", "YAPILAN KM",
                "MESAİ DIŞI KM", "İZİN DURUMU", "EN YÜKSEK HIZ", "YORUM", "ARAÇ SAHİBİ DIŞI (KM)"
            ])

            # Tarih sütununu datetime formatına çevir
            df['Tarih'] = pd.to_datetime(df['Tarih'])

            # Her bir plaka için işlem yap
            for plaka in df['Plaka'].unique():
                plaka_df = df[df['Plaka'] == plaka]

                # Sürücüyü al (ilk sürücüyü kullan)
                sürücü = plaka_df['Sürücü'].iloc[0]

                # Tarihi al (ilk tarihi kullan)
                tarih = plaka_df['Tarih'].iloc[0].strftime("%Y-%m-%d")

                # Kontak Açılma (05:00'dan sonraki ilk "Kontak Açıldı" zamanı)
                kontak_açılma_df = plaka_df[(plaka_df['Zaman'] > "05:00") & (plaka_df['İleti Tipi'] == "Kontak Açıldı")]
                if not kontak_açılma_df.empty:
                    kontak_açılma = kontak_açılma_df.sort_values(by='Zaman').iloc[0]['Zaman']
                else:
                    kontak_açılma = None  # Eğer "Kontak Açıldı" kaydı yoksa None olarak bırak

                # Gün Bitirme KM (23:59'dan önceki son "Kontak Kapalı" veya "Kontak Açıldı" zamanındaki KM)
                gün_bitirme_df = plaka_df[(plaka_df['Zaman'] <= "23:59") & (plaka_df['İleti Tipi'].isin(["Kontak Kapalı", "Kontak Açıldı"]))]
                if not gün_bitirme_df.empty:
                    gün_bitirme_km = gün_bitirme_df.sort_values(by='Zaman').iloc[-1]['Yol (km)']
                else:
                    gün_bitirme_km = None  # Eğer hiç kayıt yoksa None olarak bırak

                # İl (ilk zamana ait adresin , den önceki kısmı)
                ilk_zaman_adres = plaka_df.sort_values(by='Zaman').iloc[0]['Adres']
                if pd.isna(ilk_zaman_adres) or isinstance(ilk_zaman_adres, (float, int)):
                    il = "Bilinmiyor"  # Varsayılan değer
                else:
                    il = str(ilk_zaman_adres).split(", ")[0]  # String'e dönüştür ve split et

                # Akşam konaklama ilini al (son zamana ait adresin , den önceki kısmı)
                son_zaman_adres = plaka_df.sort_values(by='Zaman').iloc[-1]['Adres']
                if pd.isna(son_zaman_adres) or isinstance(son_zaman_adres, (float, int)):
                    akşam_konaklama_il = "Bilinmiyor"  # Varsayılan değer
                else:
                    akşam_konaklama_il = str(son_zaman_adres).split(", ")[0]  # String'e dönüştür ve split et

                # Varış saati (18:00'dan sonraki ilk "Kontak Kapalı" zamanı veya 18:00'dan önceki son "Kontak Kapalı" zamanı)
                varış_saati_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                if not varış_saati_df.empty:
                    varış_saati = varış_saati_df.sort_values(by='Zaman').iloc[0]['Zaman']
                else:
                    # Eğer 18:00'dan sonra "Kontak Kapalı" yoksa, 18:00'dan önceki son "Kontak Kapalı" verisini al
                    varış_saati_df = plaka_df[(plaka_df['Zaman'] <= "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                    if not varış_saati_df.empty:
                        varış_saati = varış_saati_df.sort_values(by='Zaman').iloc[-1]['Zaman']
                    else:
                        varış_saati = None  # Eğer hiç "Kontak Kapalı" kaydı yoksa None olarak bırak

                # Güne başlama KM (18:00'dan önceki en düşük KM)
                güne_başlama_km = plaka_df[plaka_df['Zaman'] < "18:00"]['Yol (km)'].min()

                # Yapılan KM (gün bitirme KM - güne başlama KM)
                if gün_bitirme_km is not None and güne_başlama_km is not None:
                    yapılan_km = gün_bitirme_km - güne_başlama_km
                else:
                    yapılan_km = np.nan  # Eğer gün bitirme veya güne başlama KM yoksa NaN olarak bırak

                # Mesai Dışı KM (18:00 sonrasındaki son "Kontak Kapalı" ile ilk "Kontak Açıldı" arasındaki KM farkı)
                mesai_dışı_km = 0  # Başlangıç değeri
                kontak_kapalı_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                kontak_açıldı_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Açıldı")]
                if not kontak_kapalı_df.empty and not kontak_açıldı_df.empty:
                    son_kontak_kapalı = kontak_kapalı_df.sort_values(by='Zaman').iloc[-1]  # Düzeltildi: son_kontak_kapalí -> son_kontak_kapalı
                    ilk_kontak_açıldı = kontak_açıldı_df.sort_values(by='Zaman').iloc[0]
                    mesai_dışı_km = abs(son_kontak_kapalı['Yol (km)'] - ilk_kontak_açıldı['Yol (km)'])  # Mutlak değer alındı

                # En yüksek hız (Hız (km/sa) sütunundaki maksimum değer)
                if 'Hız (km/sa)' in plaka_df.columns:
                    en_yüksek_hız = plaka_df['Hız (km/sa)'].max()  # Maksimum değeri al
                else:
                    en_yüksek_hız = np.nan  # Eğer "Hız (km/sa)" sütunu yoksa NaN olarak bırak

                # Yeni satırı oluştur
                new_row = {
                    "PLAKA": plaka,
                    "SÜRÜCÜ": sürücü,
                    "TARİH": tarih,
                    "KONTAK AÇILMA": kontak_açılma,
                    "İL": il,
                    "AKŞAM KONAKLAMA İL": akşam_konaklama_il,
                    "VARIŞ SAATİ EVE YA DA OTELE": varış_saati,
                    "GÜNE BAŞLAMA KM": güne_başlama_km,
                    "GÜN BİTİRME KM": gün_bitirme_km,
                    "YAPILAN KM": yapılan_km,
                    "MESAİ DIŞI KM": mesai_dışı_km,  # Mutlak değer olarak zaten hesaplandı
                    "İZİN DURUMU": np.nan,
                    "EN YÜKSEK HIZ": en_yüksek_hız,
                    "YORUM": np.nan,
                    "ARAÇ SAHİBİ DIŞI (KM)": np.nan
                }

                # Yeni satırı DataFrame'e ekle
                new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)

            # Dönüştürülmüş verileri ekranda göster
            st.markdown("<h2 style='text-align: center;'>Dönüştürülmüş Veriler</h2>", unsafe_allow_html=True)
            st.write(new_df)

            # Dönüştürülmüş verileri indirme butonu
            output_file = os.path.join(UPLOAD_FOLDER, f"donusturulmus_{selected_file}")
            new_df.to_excel(output_file, index=False, engine="openpyxl")

            with open(output_file, "rb") as file:
                st.download_button(
                    label="Dönüştürülmüş Verileri İndir",
                    data=file,
                    file_name=f"donusturulmus_{selected_file}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.warning("Henüz bir dönüştürülmüş dosya bulunmamaktadır.")