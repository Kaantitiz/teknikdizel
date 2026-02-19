# pages/mail_gonder.py
import streamlit as st
import pandas as pd
import win32com.client as win32
import pythoncom
import os
from io import BytesIO
from datetime import datetime

# Sayfa başlığı
st.set_page_config(page_title="Satış ve İade Raporu Mail Gönder", page_icon="✉️")
st.title("Satış ve İade Raporlarını E-Posta ile Gönder")

# Satış temsilcileri ve e-posta adresleri (GÜNCELLENMİŞ LİSTE)
SALES_REPS = {
}

# Özel mail adresleri listesi (tüm raporlar bu adreslere tek mailde gidecek)
SPECIAL_EMAILS = [
]

# Excel yükleme alanları
st.subheader("Dosya Yüklemeleri")
col1, col2 = st.columns(2)

with col1:
    sales_file = st.file_uploader("Satış Raporu Excel Dosyası (1. Dosya)", type=["xlsx", "xls"], key="sales")

with col2:
    return_file = st.file_uploader("İade Raporu Excel Dosyası (2. Dosya)", type=["xlsx", "xls"], key="returns")

if sales_file and return_file:
    try:
        # Excel'leri oku
        sales_df = pd.read_excel(sales_file)
        returns_df = pd.read_excel(return_file)
        
        # Sütun adlarını değiştir
        sales_df = sales_df.rename(columns={'TOPLAMNETFIYAT': 'SATIŞ'})
        returns_df = returns_df.rename(columns={'TOPLAMNETFIYAT': 'İADE'})
        
        # Gerekli sütunları kontrol et (URUN_ANA_GRUP eklendi)
        required_columns = ["SATISTEMSILCISI", "MARKA", "SATIŞ", "URUN_ANA_GRUP"]
        required_columns_returns = ["SATISTEMSILCISI", "MARKA", "İADE", "URUN_ANA_GRUP"]
        
        if all(col in sales_df.columns for col in required_columns) and all(col in returns_df.columns for col in required_columns_returns):
            st.success("Tüm gerekli sütunlar mevcut!")
            
            # Eksik veri kontrolü
            if sales_df[required_columns].isnull().any().any() or returns_df[required_columns_returns].isnull().any().any():
                st.warning("Uyarı: Bazı zorunlu alanlarda eksik veri bulunuyor!")
            
            # Filtreleme seçenekleri
            st.subheader("Filtreleme Seçenekleri")
            
            # Temsilci ve marka filtreleri için birleşik değerler
            all_reps = list(set(sales_df["SATISTEMSILCISI"].unique()).union(set(returns_df["SATISTEMSILCISI"].unique())))
            all_brands = list(set(sales_df["MARKA"].unique()).union(set(returns_df["MARKA"].unique())))
            all_groups = list(set(sales_df["URUN_ANA_GRUP"].unique()).union(set(returns_df["URUN_ANA_GRUP"].unique())))
            
            selected_reps = st.multiselect(
                "Satış Temsilcisi Seçin",
                options=all_reps,
                default=all_reps,
                key="filter_reps"
            )
            
            selected_brands = st.multiselect(
                "Marka Seçin",
                options=all_brands,
                default=all_brands,
                key="filter_brands"
            )
            
            selected_groups = st.multiselect(
                "Ürün Ana Grup Seçin",
                options=all_groups,
                default=all_groups,
                key="filter_groups"
            )
            
            # Filtreleme uygula
            filtered_sales = sales_df[
                (sales_df["SATISTEMSILCISI"].isin(selected_reps)) & 
                (sales_df["MARKA"].isin(selected_brands)) &
                (sales_df["URUN_ANA_GRUP"].isin(selected_groups))
            ]
            
            filtered_returns = returns_df[
                (returns_df["SATISTEMSILCISI"].isin(selected_reps)) & 
                (returns_df["MARKA"].isin(selected_brands)) &
                (returns_df["URUN_ANA_GRUP"].isin(selected_groups))
            ]
            
            # Rapor verilerini hazırla
            st.subheader("Mailde Gönderilecek Bilgiler")
            
            # Gruplandırma işlemleri (URUN_ANA_GRUP eklendi)
            sales_grouped = filtered_sales.groupby(['SATISTEMSILCISI', 'MARKA', 'URUN_ANA_GRUP']).agg({'SATIŞ': 'sum'}).reset_index()
            returns_grouped = filtered_returns.groupby(['SATISTEMSILCISI', 'MARKA', 'URUN_ANA_GRUP']).agg({'İADE': 'sum'}).reset_index()
            
            # Satış ve iadeleri birleştir
            merged_df = pd.merge(
                sales_grouped, 
                returns_grouped, 
                on=['SATISTEMSILCISI', 'MARKA', 'URUN_ANA_GRUP'], 
                how='outer'
            ).fillna(0)
            
            # Net satış hesapla
            merged_df['NET SATIŞ'] = merged_df['SATIŞ'] - merged_df['İADE']
            
            # Formatlama işlemleri
            def format_currency(x):
                return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            merged_df['SATIŞ'] = merged_df['SATIŞ'].apply(format_currency)
            merged_df['İADE'] = merged_df['İADE'].apply(format_currency)
            merged_df['NET SATIŞ'] = merged_df['NET SATIŞ'].apply(format_currency)
            
            # Görüntüleme sırasını ayarla
            merged_df = merged_df[['SATISTEMSILCISI', 'MARKA', 'URUN_ANA_GRUP', 'SATIŞ', 'İADE', 'NET SATIŞ']]
            
            st.dataframe(merged_df)
            
            # Bugünün tarihini al
            current_date = datetime.now()
            formatted_date = current_date.strftime("%d/%m/%Y")
            
            # E-posta gönderme butonu
            if st.button("Raporları Gönder"):
                try:
                    # COM başlatma
                    pythoncom.CoInitialize()
                    
                    outlook = win32.Dispatch('Outlook.Application')
                    progress_bar = st.progress(0)
                    total_reps = len(SALES_REPS)
                    processed_count = 0
                    success_count = 0
                    error_count = 0
                    
                    # Sonuçları saklamak için liste
                    results = []
                    
                    # Tüm raporları birleştirerek tek bir HTML içeriği oluştur
                    all_reports_html = ""
                    
                    # Her satış temsilcisi için rapor oluştur
                    for rep_name, rep_email in SALES_REPS.items():
                        try:
                            # Temsilciye ait raporları filtrele
                            rep_data = merged_df[merged_df["SATISTEMSILCISI"] == rep_name]
                            
                            if len(rep_data) == 0:
                                results.append(f"⚠ {rep_name} için rapor verisi bulunamadı")
                                processed_count += 1
                                progress_bar.progress(processed_count / total_reps)
                                continue
                            
                            # SATISTEMSILCISI sütununu çıkar
                            report_df = rep_data[['MARKA', 'URUN_ANA_GRUP', 'SATIŞ', 'İADE', 'NET SATIŞ']]
                            
                            # HTML tablosu oluştur
                            html_table = report_df.to_html(
                                index=False,
                                classes="dataframe",
                                border=0,
                                justify='left'
                            )
                            
                            # Toplamları hesapla (formatlanmamış değerlerle)
                            total_sales = filtered_sales[filtered_sales["SATISTEMSILCISI"] == rep_name]["SATIŞ"].sum()
                            total_returns = filtered_returns[filtered_returns["SATISTEMSILCISI"] == rep_name]["İADE"].sum()
                            net_sales = total_sales - total_returns
                            
                            # Formatla
                            formatted_sales = format_currency(total_sales)
                            formatted_returns = format_currency(total_returns)
                            formatted_net = format_currency(net_sales)
                            
                            # Bireysel rapor HTML'i
                            individual_report = f"""
                            <div style="margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 20px;">
                                <h3 style="color: #2E86C1;">{rep_name.split('.')[0].capitalize()} Raporu</h3>
                                <p><strong>Alıcı:</strong> {rep_email}</p>
                                {html_table}
                                <p class="total">Toplam Satış: {formatted_sales} TL</p>
                                <p class="total">Toplam İade: <span style="color: red;">{formatted_returns} TL</span></p>
                                <p class="total">Net Satış: {formatted_net} TL</p>
                            </div>
                            """
                            
                            all_reports_html += individual_report
                            
                            # Temsilciye ayrı mail gönder
                            mail_to_rep = outlook.CreateItem(0)
                            mail_to_rep.To = rep_email
                            mail_to_rep.Subject = f"{rep_name.split('.')[0].capitalize()} - MARKA BAZLI SATIŞ RAPORU"
                            mail_to_rep.HTMLBody = f"""
                            <html>
                                <head>
                                    <style>
                                        table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
                                        th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
                                        th {{ background-color: #f2f2f2; }}
                                        .total {{ font-weight: bold; font-size: 1.1em; }}
                                        .negative {{ color: red; }}
                                    </style>
                                </head>
                                <body>
                                    <p>Merhaba {rep_name.split('.')[0].capitalize()},</p>
                                    <p>Aşağıda size ait marka ve ürün grubu bazlı satış raporu bulunmaktadır:</p>
                                    <p><b>Aşağıda bulunan verilere KDV dahil değildir.</b></p>
                                    {html_table}
                                    <p class="total">Toplam Satış: {formatted_sales} TL</p>
                                    <p class="total">Toplam İade: <span class="negative">{formatted_returns} TL</span></p>
                                    <p class="total">Net Satış: {formatted_net} TL</p>
                                    <p style="font-style: italic; color: #555555;">* Bu rapor {formatted_date} tarihine kadar olan verileri içermektedir.</p>
                                    <p>İyi çalışmalar dileriz,</p>
                                    <p>Satış Yönetim Ekibi</p>
                                </body>
                            </html>
                            """
                            mail_to_rep.Send()
                            
                            results.append(f"✅ {rep_name} ({rep_email}) raporu gönderildi")
                            success_count += 1
                            
                        except Exception as e:
                            results.append(f"❌ {rep_name} ({rep_email}) gönderilemedi: {str(e)}")
                            error_count += 1
                        
                        processed_count += 1
                        progress_bar.progress(processed_count / total_reps)
                    
                    # Özel mail adreslerine tüm raporları tek mailde gönder
                    for special_email in SPECIAL_EMAILS:
                        try:
                            summary_mail = outlook.CreateItem(0)
                            summary_mail.To = special_email
                            summary_mail.Subject = f"TÜM SATIŞ TEMSİLCİLERİ RAPORLARI - {formatted_date}"
                            summary_mail.HTMLBody = f"""
                            <html>
                                <head>
                                    <style>
                                        table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
                                        th, td {{ border: 1px solid #dddddd; text-align: left; padding: 8px; }}
                                        th {{ background-color: #f2f2f2; }}
                                        .total {{ font-weight: bold; font-size: 1.1em; }}
                                        .negative {{ color: red; }}
                                        .report-section {{ margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 20px; }}
                                        .header {{ color: #2E86C1; font-size: 1.2em; }}
                                    </style>
                                </head>
                                <body>
                                    <h2 class="header">Tüm Satış Temsilcileri Raporları</h2>
                                    <p><strong>Rapor Tarihi:</strong> {formatted_date}</p>
                                    <p><strong>Toplam Temsilci Sayısı:</strong> {len(SALES_REPS)}</p>
                                    {all_reports_html}
                                    <p style="font-style: italic; color: #555555; margin-top: 30px;">
                                        * Bu rapor {formatted_date} tarihine kadar olan verileri içermektedir.
                                    </p>
                                    <p>İyi çalışmalar dileriz,</p>
                                    <p>Satış Yönetim Ekibi</p>
                                </body>
                            </html>
                            """
                            summary_mail.Send()
                            results.append(f"📨 Tüm raporlar özet olarak {special_email} adresine gönderildi")
                            success_count += 1
                        except Exception as e:
                            results.append(f"❌ Özet rapor {special_email} adresine gönderilemedi: {str(e)}")
                            error_count += 1
                    
                    # Sonuçları göster
                    st.subheader("Gönderim Sonuçları")
                    for result in results:
                        st.write(result)
                    
                    st.success(f"İşlem tamamlandı! Başarılı: {success_count}, Başarısız: {error_count}")
                    
                except Exception as e:
                    st.error(f"Outlook bağlantı hatası: {str(e)}")
                finally:
                    # COM temizleme
                    pythoncom.CoUninitialize()
        else:
            missing_in_sales = [col for col in required_columns if col not in sales_df.columns]
            missing_in_returns = [col for col in required_columns_returns if col not in returns_df.columns]
            missing_cols = missing_in_sales + missing_in_returns
            st.error(f"Hata: Excel dosyalarında gerekli sütunlar bulunamadı. Eksik sütunlar: {', '.join(missing_cols)}")
            
    except Exception as e:
        st.error(f"Excel okuma hatası: {str(e)}")
else:

    st.info("Lütfen hem satış hem de iade raporu içeren Excel dosyalarını yükleyiniz.")
