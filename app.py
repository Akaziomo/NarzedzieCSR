# app.py - Narzędzie Oceny CSR w Logistyce (Wersja 2.0)

import streamlit as st
import pandas as pd

# ----------------------------------------------------------------------
# 1. DEFINICJA PYTAŃ I PUNKTACJI (Twój Model)
# Definiujemy tu Poziom 0 (brak CSR) oraz Poziomy 1-5
# Poziomy: 0 - Brak CSR, 1 - Wczesny Rozwój, 2 - Transformacja, 3 - Integracja, 4 - Dojrzałość, 5 - Innowacyjne Przywództwo
# ----------------------------------------------------------------------

pytania_df = pd.DataFrame({
    'Pytanie': [
        # Pytanie 1: Zespół roboczy ds. zarządzania środowiskowego
        "Czy w przedsiębiorstwie funkcjonuje zespół roboczy zajmujący się zarządzaniem środowiskowym?",
        
        # Pytanie 2: Zespół roboczy ds. zarządzania środowiskowego (spotkania)
        "Czy w przedsiębiorstwie funkcjonuje zespół roboczy zajmujący się zarządzaniem środowiskowym, odbywający regularne spotkania?",
        
        # Pytanie 3: Zespół roboczy ds. działań proekologicznych (cel)
        "W przedsiębiorstwie funkcjonuje zespół roboczy zajmujący się zarządzaniem środowiskowym, odbywający regularne spotkania w celu omawiania działalności proekologicznej?",
        
        # Pytanie 4: Procent surowców zrównoważonych
        "Jaki procent surowców wykorzystywanych do produkcji należy do zrównoważonych surowców półproduktów i materiałów obejmujących koncepcję użycia materiałów odnawialnych, biodegradowalnych i pochodzących z recyklingu?"
    ],
    'Klucz': ['q_zespol_ogolny', 'q_zespol_spotkania', 'q_zespol_cel', 'q_surowce'],
    
    # Opcje i przypisane im punkty (używamy punktów jako klucza do Poziomu)
    'Opcje_Punkty': [
        {'Tak': 2, 'Nie': 1}, # Pytanie 1 (Poziom 2 lub Poziom 1)
        {'Tak': 3, 'Nie': 2}, # Pytanie 2 (Poziom 3 lub Poziom 2)
        {'Tak': 4, 'Nie': 3}, # Pytanie 3 (Poziom 4 lub Poziom 3)
        {  # Pytanie 4: Skala punktowa
            '0%': 0, '1%-9%': 1, '10%-30%': 2, '30%-50%': 3, 
            '50%-85%': 4, '85% <': 5
        }
    ],
    
    # Przypisanie: Ile punktów odpowiada któremu Poziomowi (Wartość_Punktowa: Numer_Poziomu)
    # 0 pkt trafia do Poziomu 0; Punkty 1-5 trafiają do Poziomów 1-5
    'Przypisanie_Poziomów': [
        {2: 2, 1: 1}, 
        {3: 3, 2: 2}, 
        {4: 4, 3: 3}, 
        {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5} 
    ]
})

# ----------------------------------------------------------------------
# 2. INTERFEJS UŻYTKOWNIKA (Streamlit)
# ----------------------------------------------------------------------

st.set_page_config(page_title="Narzędzie Oceny CSR w Logistyce", layout="wide") # Używamy 'wide' dla tabel

st.title("🌱 Narzędzie Oceny Zrównoważonej Logistyki (CSR)")
st.markdown("Proszę odpowiedzieć na poniższe pytania, aby określić poziom dojrzałości CSR w Państwa procesach logistycznych.")

# Słownik do przechowywania sumy punktów dla każdego poziomu (włącznie z Poziomem 0)
wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
poziomy_nazwy = {
    0: "🛑 Brak Formalnego CSR (Poziom 0)", 
    1: "🟢 Wczesny Rozwój (Poziom 1)", 
    2: "🔵 Transformacja (Poziom 2)", 
    3: "🟠 Integracja (Poziom 3)", 
    4: "🟣 Dojrzałość (Poziom 4)", 
    5: "💎 Innowacyjne Przywództwo (Poziom 5)"
}


with st.form("formularz_oceny"):
    
    st.header("Kryteria I: Struktura Organizacyjna i Procesy (Poziomy 1-4)")
    
    for index, row in pytania_df.iterrows():
        st.subheader(f"Pytanie {index + 1}: {row['Pytanie']}")
        
        # Lista opcji wyświetlanych dla użytkownika
        opcje_list = list(row['Opcje_Punkty'].keys())
        
        # Wyświetlanie przycisków radiowych/opcji
        wybrana_opcja_label = st.radio(
            "Wybierz odpowiedź:", 
            opcje_list, 
            key=row['Klucz'] 
        )
        
        # Obliczenia: przypisywanie punktów i sumowanie
        punkty_za_odpowiedz = row['Opcje_Punkty'][wybrana_opcja_label]
        
        # Przypisujemy te punkty do odpowiedniego Poziomu
        przypisany_poziom = row['Przypisanie_Poziomów'][punkty_za_odpowiedz]
        
        # Sumujemy punkty dla danego poziomu
        wyniki_poziomow[przypisany_poziom] += punkty_za_odpowiedz

    # Przycisk zatwierdzający formularz
    submitted = st.form_submit_button("Oblicz Poziom Zrównoważonego Rozwoju")


# ----------------------------------------------------------------------
# 3. WYNIKI I INTELIGENTNE PODSUMOWANIE (Logika)
# ----------------------------------------------------------------------

if submitted:
    st.balloons()
    st.header("📊 Wynik Oceny i Rekomendacje")
    
    # 1. Wyszukanie Poziomu Dominującego
    # Usuwamy Poziom 0 z listy, jeśli ma 0 punktów
    punkty_do_analizy = {p: pkt for p, pkt in wyniki_poziomow.items() if pkt > 0 or p == 0} 
    
    # Szukamy Poziomu, który uzyskał największą sumę punktów
    dominujacy_poziom = max(punkty_do_analizy, key=punkty_do_analizy.get)
    max_punkty = wyniki_poziomow[dominujacy_poziom]
    
    st.success(f"## 🏆 Osiągnięty Poziom Dojrzałości: {poziomy_nazwy[dominujacy_poziom]}")
    st.subheader(f"Suma punktów dla Poziomu {dominujacy_poziom}: **{max_punkty}**")
    
    st.markdown("---")

    # 2. Wyświetlenie szczegółowej punktacji w tabeli
    st.subheader("Szczegółowa Punktacja dla Każdego Poziomu:")
    df_wyniki = pd.DataFrame(
        list(wyniki_poziomow.items()), 
        columns=['Poziom', 'Suma Punktów']
    )
    df_wyniki['Nazwa Poziomu'] = df_wyniki['Poziom'].map(poziomy_nazwy)
    
    # Przenosimy kolumnę Nazwa Poziomu na przód
    df_wyniki = df_wyniki[['Poziom', 'Nazwa Poziomu', 'Suma Punktów']]
    
    # Wyróżnienie dominującego poziomu
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: #d4edda' if v else '' for v in is_max]
    
    st.dataframe(
        df_wyniki.style.apply(highlight_max, subset=['Suma Punktów']),
        hide_index=True
    )

    # 3. Generowanie Inteligentnego Podsumowania (W ramach Pracy Inżynierskiej to rozbudujesz!)
    st.subheader("Wnioski i Rekomendacje:")
    
    # Przykład: Podsumowanie na podstawie dominującego poziomu
    if dominujacy_poziom == 0:
        st.error("### 🛑 Wymagane Natychmiastowe Działania!")
        st.write("Brak formalnych struktur i mierników wskazuje na niewypełnianie podstawowych wymogów. Należy jak najszybciej powołać zespół roboczy i ustalić minimalne standardy zgodności z przepisami.")
    elif dominujacy_poziom == 1:
        st.info("### 🟢 Kierunek Rozwoju")
        st.write("Organizacja wykazuje wstępną świadomość. Rekomendacja: Formalizacja spotkań zespołu oraz jasne zdefiniowanie, jakie mierniki proekologiczne są kluczowe dla logistyki.")
    # ... dodaj własne rozbudowane analizy i wnioski dla Poziomów 2, 3, 4 i 5, opierając się na punktacji!