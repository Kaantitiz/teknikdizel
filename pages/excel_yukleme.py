import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from collections import defaultdict

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
            
            df = pd.read_excel(file_path)
            df['Sürücü'] = df['Sürücü'].fillna("Dağıtım Aracı")

            if 'Hız (km/sa) ' in df.columns:
                df['Hız (km/sa) '] = df['Hız (km/sa) '].astype(str).str.replace(',', '').astype(float)
            if 'Yol (km)' in df.columns:
                df['Yol (km)'] = df['Yol (km)'].astype(str).str.replace(',', '').astype(float)

            new_df = pd.DataFrame(columns=[
                "PLAKA", "SÜRÜCÜ", "TARİH", "KONTAK AÇILMA", "İL", "AKŞAM KONAKLAMA İL",
                "VARIŞ SAATİ EVE YA DA OTELE", "GÜNE BAŞLAMA KM", "GÜN BİTİRME KM", "YAPILAN KM",
                "MESAİ DIŞI KM", "GECE KULLANIMI", "İZİN DURUMU", "EN YÜKSEK HIZ", "YORUM", "ARAÇ SAHİBİ DIŞI (KM)"
            ])

            df['Tarih'] = pd.to_datetime(df['Tarih'])

            for plaka in df['Plaka'].unique():
                plaka_df = df[df['Plaka'] == plaka]
                sürücü = plaka_df['Sürücü'].iloc[0]
                tarih = plaka_df['Tarih'].iloc[0].strftime("%Y-%m-%d")

                # Kontak Açılma
                kontak_açılma_df = plaka_df[(plaka_df['Zaman'] > "05:00") & (plaka_df['İleti Tipi'] == "Kontak Açıldı")]
                kontak_açılma = kontak_açılma_df.sort_values(by='Zaman').iloc[0]['Zaman'] if not kontak_açılma_df.empty else None

                # Gün Bitirme KM
                gün_bitirme_df = plaka_df[(plaka_df['Zaman'] <= "23:59") & (plaka_df['İleti Tipi'].isin(["Kontak Kapalı", "Kontak Açıldı"]))]
                gün_bitirme_km = gün_bitirme_df.sort_values(by='Zaman').iloc[-1]['Yol (km)'] if not gün_bitirme_df.empty else None

                # İl bilgisi
                ilk_zaman_adres = plaka_df.sort_values(by='Zaman').iloc[0]['Adres']
                il = str(ilk_zaman_adres).split(", ")[0] if not pd.isna(ilk_zaman_adres) and isinstance(ilk_zaman_adres, str) else "Bilinmiyor"

                # Akşam konaklama ili
                son_zaman_adres = plaka_df.sort_values(by='Zaman').iloc[-1]['Adres']
                akşam_konaklama_il = str(son_zaman_adres).split(", ")[0] if not pd.isna(son_zaman_adres) and isinstance(son_zaman_adres, str) else "Bilinmiyor"

                # Varış saati
                varış_saati_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                if not varış_saati_df.empty:
                    varış_saati = varış_saati_df.sort_values(by='Zaman').iloc[0]['Zaman']
                else:
                    varış_saati_df = plaka_df[(plaka_df['Zaman'] <= "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                    varış_saati = varış_saati_df.sort_values(by='Zaman').iloc[-1]['Zaman'] if not varış_saati_df.empty else None

                # Güne başlama KM
                güne_başlama_km = plaka_df[plaka_df['Zaman'] < "18:00"]['Yol (km)'].min()

                # Yapılan KM
                yapılan_km = gün_bitirme_km - güne_başlama_km if gün_bitirme_km is not None and güne_başlama_km is not None else np.nan

                # Mesai Dışı KM
                mesai_dışı_km = 0
                kontak_kapalı_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Kapalı")]
                kontak_açıldı_df = plaka_df[(plaka_df['Zaman'] > "18:00") & (plaka_df['İleti Tipi'] == "Kontak Açıldı")]
                if not kontak_kapalı_df.empty and not kontak_açıldı_df.empty:
                    son_kontak_kapalı = kontak_kapalı_df.sort_values(by='Zaman').iloc[-1]
                    ilk_kontak_açıldı = kontak_açıldı_df.sort_values(by='Zaman').iloc[0]
                    mesai_dışı_km = abs(son_kontak_kapalı['Yol (km)'] - ilk_kontak_açıldı['Yol (km)'])

                # Gece kullanımı kontrolü (00:00-06:00 arası)
                def check_night_usage(plaka_df):
                    night_events = plaka_df[
                        (plaka_df['Zaman'] >= "00:00") & 
                        (plaka_df['Zaman'] < "06:00") & 
                        (plaka_df['İleti Tipi'].isin(["Kontak Açıldı", "Kontak Kapalı"]))
                    ]
                    return "Kullanıldı" if not night_events.empty else "Kullanılmadı"

                # En yüksek hız hesaplama
                if 'Hız (km/sa) ' in plaka_df.columns:
                    try:
                        hiz_verileri = (
                            plaka_df['Hız (km/sa) ']
                            .astype(str)
                            .str.replace(',', '.')
                            .replace(r'[^\d.]', '', regex=True)
                            .replace('', np.nan)
                            .replace('0', np.nan)
                            .dropna()
                            .astype(float)
                        )
                        
                        if not hiz_verileri.empty:
                            en_yüksek_hız = hiz_verileri.max()
                            en_yüksek_hız = f"{en_yüksek_hız:.2f}".replace('.', ',')
                        else:
                            en_yüksek_hız = "0"
                            
                    except Exception as e:
                        st.error(f"Hız hesaplama hatası: {str(e)}")
                        en_yüksek_hız = "Hesaplanamadı"
                else:
                    en_yüksek_hız = "Sütun Yok"

                # YORUM sütunu - GÜNCELLENMİŞ VERSİYON
                yorum = ""
                previous_location = None
                location_changes = []

                kontak_events = plaka_df[plaka_df['İleti Tipi'].isin(["Kontak Açıldı", "Kontak Kapalı"])].sort_values(by='Zaman')
                for _, event in kontak_events.iterrows():
                    current_address = event['Adres']
                    if pd.isna(current_address) or isinstance(current_address, (float, int)):
                        current_location = "Bilinmiyor"
                    else:
                        parts = [p.strip() for p in str(current_address).split(",") if p.strip()]
                        if len(parts) >= 2:
                            current_location = (parts[0], parts[1])  # (il, ilçe) tuple'ı olarak sakla
                        else:
                            current_location = (parts[0], "") if parts else ("Bilinmiyor", "")
                    
                    if previous_location is None or current_location != previous_location:
                        location_changes.append(current_location)
                        previous_location = current_location

                if location_changes:
                    # Şehirleri grupla
                    city_districts = defaultdict(list)
                    for city, district in location_changes:
                        if city and district:  # Hem il hem ilçe varsa
                            city_districts[city].append(district)
                    
                    # İstanbul ve Ankara için özel işlem
                    istanbul_districts = []
                    ankara_districts = []
                    other_cities = []
                    
                    for city, districts in city_districts.items():
                        if "İstanbul" in city:
                            istanbul_districts.extend(districts)
                        elif "Ankara" in city:
                            ankara_districts.extend(districts)
                        else:
                            # Diğer şehirler için il - ilçe, ilçe formatı
                            unique_districts = sorted(list(set(districts)))
                            if unique_districts:
                                other_cities.append(f"{city}: {', '.join(unique_districts)}")
                            else:
                                other_cities.append(city)
                    
                    # Yorum parçalarını oluştur
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
    else:
        st.warning("Henüz bir dönüştürülmüş dosya bulunmamaktadır.")
