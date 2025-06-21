import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
from collections import defaultdict

# Sayfa başlığı ve ikonu
st.set_page_config(page_title="Excel Yönetimi ve Dönüştürme", page_icon="📊", layout="wide")

st.markdown("<h1 style='text-align: center;'>Excel Yönetimi ve Dönüştürme</h1>", unsafe_allow_html=True)

# Klasör ayarları
UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Yardımcı fonksiyonlar
def clean_numeric_value(value):
    """Convert string numbers with commas to float"""
    if pd.isna(value) or value == '':
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = re.sub(r'[^\d.,]', '', str(value))
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except (ValueError, TypeError):
        return np.nan

def parse_address(address):
    """Parse address into city and district"""
    if pd.isna(address) or not isinstance(address, str):
        return ("Bilinmiyor", "")
    
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 2:
        return (parts[0], parts[1])
    elif len(parts) == 1:
        return (parts[0], "")
    else:
        return ("Bilinmiyor", "")

def check_night_usage(plaka_df):
    """Check if vehicle was used between 00:00-06:00"""
    night_events = plaka_df[
        (plaka_df['Zaman'] >= "00:00") & 
        (plaka_df['Zaman'] < "06:00") & 
        (plaka_df['İleti Tipi'].isin(["Kontak Açıldı", "Kontak Kapalı"]))
    ]
    return "Kullanıldı" if not night_events.empty else "Kullanılmadı"

# Kullanıcı seçimi: Yeni dosya yükle veya mevcut bir dosyayı seç
option = st.radio(
    "Seçim Yapın:",
    ("Yeni Excel Dosyası Yükle", "Kayıtlı Bir Dosyayı Seç")
)

uploaded_file = None
selected_file = None

if option == "Yeni Excel Dosyası Yükle":
    # Tarih seçimi
    selected_date = st.date_input("Lütfen tarih seçin", value=None)

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
            date_str = selected_date.strftime("%Y-%m-%d")
            file_name = f"{date_str}.xlsx"
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            
            if os.path.exists(file_path):
                st.warning(f"Bu dosya zaten sistemde bulunuyor: {file_name}")
            else:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Dosyanız başarıyla eklenmiştir. Dosya Adı: {file_name}")

elif option == "Kayıtlı Bir Dosyayı Seç":
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith((".xlsx", ".xls"))]
    
    def is_valid_date_format(filename):
        try:
            date_part = filename.split(".")[0]
            datetime.strptime(date_part, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    valid_files = [f for f in files if is_valid_date_format(f)]
    
    if valid_files:
        files_with_prompt = ["Lütfen bir dosya seçin"] + valid_files
        selected_file = st.selectbox("Bir dosya seçin:", files_with_prompt)
        
        if selected_file != "Lütfen bir dosya seçin":
            st.info(f"Seçilen dosya işleniyor: {selected_file}")
            file_path = os.path.join(UPLOAD_FOLDER, selected_file)
            
            try:
                df = pd.read_excel(file_path)
                df['Sürücü'] = df['Sürücü'].fillna("Dağıtım Aracı")

                # Clean numeric columns
                numeric_cols = ['Hız (km/sa) ', 'Yol (km)']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = df[col].apply(clean_numeric_value)

                new_df = pd.DataFrame(columns=[
                    "PLAKA", "SÜRÜCÜ", "TARİH", "KONTAK AÇILMA", "İL", "AKŞAM KONAKLAMA İL",
                    "VARIŞ SAATİ EVE YA DA OTELE", "GÜNE BAŞLAMA KM", "GÜN BİTİRME KM", "YAPILAN KM",
                    "MESAİ DIŞI KM", "GECE KULLANIMI", "İZİN DURUMU", "EN YÜKSEK HIZ", "YORUM", "ARAÇ SAHİBİ DIŞI (KM)"
                ])

                df['Tarih'] = pd.to_datetime(df['Tarih'])

                for plaka in df['Plaka'].unique():
                    plaka_df = df[df['Plaka'] == plaka].copy()
                    sürücü = plaka_df['Sürücü'].iloc[0]
                    tarih = plaka_df['Tarih'].iloc[0].strftime("%Y-%m-%d")

                    # Kontak Açılma
                    kontak_açılma_df = plaka_df[(plaka_df['Zaman'] > "05:00") & (plaka_df['İleti Tipi'] == "Kontak Açıldı")]
                    kontak_açılma = kontak_açılma_df.sort_values(by='Zaman').iloc[0]['Zaman'] if not kontak_açılma_df.empty else None

                    # Gün Bitirme KM
                    gün_bitirme_df = plaka_df[(plaka_df['Zaman'] <= "23:59") & (plaka_df['İleti Tipi'].isin(["Kontak Kapalı", "Kontak Açıldı"]))]
                    gün_bitirme_km = clean_numeric_value(
                        gün_bitirme_df.sort_values(by='Zaman').iloc[-1]['Yol (km)'] if not gün_bitirme_df.empty else None
                    )

                    # İl bilgisi
                    ilk_zaman_adres = plaka_df.sort_values(by='Zaman').iloc[0]['Adres']
                    il = parse_address(ilk_zaman_adres)[0]

                    # Akşam konaklama ili
                    son_zaman_adres = plaka_df.sort_values(by='Zaman').iloc[-1]['Adres']
                    akşam_konaklama_il = parse_address(son_zaman_adres)[0]

                    # Varış saati
                    varış_saati_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                    if not varış_saati_df.empty:
                        varış_saati = varış_saati_df.sort_values(by='Zaman').iloc[0]['Zaman']
                    else:
                        varış_saati_df = plaka_df[(plaka_df['Zaman'] <= "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                        varış_saati = varış_saati_df.sort_values(by='Zaman').iloc[-1]['Zaman'] if not varış_saati_df.empty else None

                    # Güne başlama KM
                    güne_başlama_df = plaka_df[plaka_df['Zaman'] < "18:00"]
                    güne_başlama_km = clean_numeric_value(
                        güne_başlama_df['Yol (km)'].min() if not güne_başlama_df.empty else None
                    )

                    # Yapılan KM
                    try:
                        yapılan_km = float(gün_bitirme_km) - float(güne_başlama_km) if pd.notna(gün_bitirme_km) and pd.notna(güne_başlama_km) else np.nan
                    except (ValueError, TypeError):
                        yapılan_km = np.nan

                    # Mesai Dışı KM
                    mesai_dışı_km = 0
                    kontak_kapalı_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                    kontak_açıldı_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Açıldı")]
                    
                    if not kontak_kapalı_df.empty and not kontak_açıldı_df.empty:
                        son_kontak_kapalı = kontak_kapalı_df.sort_values(by='Zaman').iloc[-1]
                        ilk_kontak_açıldı = kontak_açıldı_df.sort_values(by='Zaman').iloc[0]
                        try:
                            mesai_dışı_km = abs(clean_numeric_value(son_kontak_kapalı['Yol (km)']) - clean_numeric_value(ilk_kontak_açıldı['Yol (km)']))
                        except (ValueError, TypeError):
                            mesai_dışı_km = 0

                    # En yüksek hız hesaplama
                    if 'Hız (km/sa) ' in plaka_df.columns:
                        try:
                            hiz_verileri = plaka_df['Hız (km/sa) '].dropna()
                            if not hiz_verileri.empty:
                                en_yüksek_hız = f"{hiz_verileri.max():.2f}".replace('.', ',')
                            else:
                                en_yüksek_hız = "0"
                        except Exception as e:
                            st.error(f"Hız hesaplama hatası: {str(e)}")
                            en_yüksek_hız = "Hesaplanamadı"
                    else:
                        en_yüksek_hız = "Sütun Yok"

                    # YORUM sütunu
                    yorum = ""
                    location_changes = []
                    previous_location = None

                    kontak_events = plaka_df[plaka_df['İleti Tipi'].isin(["Kontak Açıldı", "Kontak Kapalı"])].sort_values(by='Zaman')
                    for _, event in kontak_events.iterrows():
                        current_location = parse_address(event['Adres'])
                        if previous_location is None or current_location != previous_location:
                            location_changes.append(current_location)
                            previous_location = current_location

                    if location_changes:
                        city_districts = defaultdict(list)
                        for city, district in location_changes:
                            if district:  # Sadece boş olmayan ilçeleri ekle
                                city_districts[city].append(district)
                        
                        istanbul_districts = []
                        ankara_districts = []
                        other_cities = []
                        
                        for city, districts in city_districts.items():
                            if "İstanbul" in city:
                                istanbul_districts.extend(districts)
                            elif "Ankara" in city:
                                ankara_districts.extend(districts)
                            else:
                                unique_districts = sorted(list(set(districts)))
                                if unique_districts:
                                    other_cities.append(f"{city}: {', '.join(unique_districts)}")
                                else:
                                    other_cities.append(city)
                        
                        yorum_parts = []
                        
                        if istanbul_districts:
                            unique_districts = sorted(list(set(istanbul_districts)))
                            yorum_parts.append("İSTANBUL: " + ", ".join(unique_districts))
                        
                        if ankara_districts:
                            unique_districts = sorted(list(set(ankara_districts)))
                            yorum_parts.append("ANKARA: " + ", ".join(unique_districts))
                        
                        if other_cities:
                            yorum_parts.append(" " + " | ".join(other_cities))
                        
                        yorum = " | ".join(yorum_parts) if yorum_parts else "Araç Kullanılmadı"
                    else:
                        yorum = "Araç Kullanılmadı"

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
                        "MESAİ DIŞI KM": mesai_dışı_km,
                        "GECE KULLANIMI": check_night_usage(plaka_df),
                        "İZİN DURUMU": np.nan,
                        "EN YÜKSEK HIZ": en_yüksek_hız,
                        "YORUM": yorum,
                        "ARAÇ SAHİBİ DIŞI (KM)": np.nan
                    }

                    new_df = pd.concat([new_df, pd.DataFrame([new_row])], ignore_index=True)

                st.markdown("<h2 style='text-align: center;'>Dönüştürülmüş Veriler</h2>", unsafe_allow_html=True)
                st.write(new_df)

                output_file = os.path.join(UPLOAD_FOLDER, f"donusturulmus_{selected_file}")
                new_df.to_excel(output_file, index=False, engine="openpyxl")

                with open(output_file, "rb") as file:
                    st.download_button(
                        label="Dönüştürülmüş Verileri İndir",
                        data=file,
                        file_name=f"donusturulmus_{selected_file}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error(f"Dosya işlenirken hata oluştu: {str(e)}")
    else:
        st.warning("Henüz bir dönüştürülmüş dosya bulunmamaktadır.")
