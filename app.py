# app.py - Narzędzie Oceny CSR w Logistyce wersja 4.2

import streamlit as st
import pandas as pd
import time

# ----------------------------------------------------------------------
# 0. FUNKCJE POMOCNICZE
# ----------------------------------------------------------------------

def initialize_anchor():
    if 'top_anchor' not in st.session_state:
        st.session_state.top_anchor = st.empty()

def scroll_to_top():
    """Wymusza przewinięcie do elementu kotwicy na samej górze strony."""
    if 'top_anchor' in st.session_state:
        time.sleep(0.01)
        st.session_state.top_anchor.empty()

# Funkcja do obliczania punktów na podstawie wybranych opcji
def calculate_scores(pytania_df):
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for index, row in pytania_df.iterrows():
        klucz_pytania = row['Klucz']
        
        wybrana_opcja_label = st.session_state.get(klucz_pytania)

        if wybrana_opcja_label is not None:
            
            punkty_za_odpowiedz_id = row['Opcje_Punkty'][wybrana_opcja_label]

            przypisany_poziom = row['Przypisanie_Poziomów'][punkty_za_odpowiedz_id]
            
            if przypisany_poziom > 0:
                st.session_state.wyniki_poziomow[przypisany_poziom] += 1
                
def go_to_test():
    st.session_state["page"] = "test"
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    scroll_to_top()


# ----------------------------------------------------------------------
# 1. DEFINICJA PYTAŃ, PUNKTACJI I OPISÓW POZIOMÓW
# ----------------------------------------------------------------------

pytania_df = pd.DataFrame({
    'Pytanie': [
        "1. Czy w przedsiębiorstwie funkcjonuje zespół roboczy zajmujący się zarządzaniem środowiskowym?",
        "2. Czy w przedsiębiorstwie funkcjonuje zespół roboczy zajmujący się zarządzaniem środowiskowym, odbywający regularne spotkania?",
        "3. W przedsiębiorstwie funkcjonuje zespół roboczy zajmujący się zarządzaniem środowiskowym, odbywający regularne spotkania w celu omawiania działalności proekologicznej?",
        "4. Jaki procent surowców wykorzystywanych do produkcji należy do zrównoważonych surowców półproduktów i materiałów obejmujących koncepcję użycia materiałów odnawialnych, biodegradowalnych i pochodzących z recyklingu?"
    ],
    'Klucz': [
        'q_zespol_ogolny', 'q_zespol_spotkania', 'q_zespol_cel', 'q_surowce'
    ],
    
    'Opcje_Punkty': [
        {'Tak': 2, 'Nie': 1},
        {'Tak': 2, 'Nie': 1},
        {'Tak': 3, 'Nie': 1},
        {'0%': 0, '1%-9%': 1, '10%-30%': 2, '30%-50%': 3, '50%-85%': 4, '85% <': 5}
    ],
    
    'Przypisanie_Poziomów': [
        {2: 2, 1: 1},
        {2: 2, 1: 1},
        {3: 3, 1: 1},
        {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
    ]
})

poziomy_nazwy = {
    0: "Brak Formalnego CSR (Poziom 0)", 
    1: "Wczesny Rozwój (Poziom 1)", 
    2: "Transformacja (Poziom 2)", 
    3: "Integracja (Poziom 3)", 
    4: "Dojrzałość (Poziom 4)", 
    5: "Innowacyjne Przywództwo (Poziom 5)"
}

poziomy_opisy = {
    0: "W firmie nie istnieją formalne struktury ani działania mające na celu zarządzanie zrównoważonym rozwojem i CSR. Działania proekologiczne, jeśli występują, są incydentalne i nieskoordynowane.",
    1: "Firma ma wstępną świadomość potrzeby działań CSR. Powołano pojedyncze inicjatywy lub zespół, ale brakuje systematyczności, regularnych spotkań i jasno określonych celów strategicznych.",
    2: "W firmie rozpoczęto proces formalizacji działań. Funkcjonuje zespół roboczy, który spotyka się regularnie. Jednak działania mogą być nadal reaktywne, a integracja zrównoważonych surowców jest na niskim poziomie.",
    3: "Zrównoważony rozwój jest częściowo zintegrowany z procesami operacyjnymi i celami. Zespół roboczy omawia konkretne działania proekologiczne, a udział zrównoważonych surowców zaczyna być zauważalny (10%-50%).",
    4: "Dojrzałe zarządzanie CSR. Zrównoważony rozwój jest elementem strategii, a monitoring postępów jest systematyczny. Firma aktywnie zwiększa udział zrównoważonych surowców (50%-85%) i dąży do ciągłej poprawy.",
    5: "Firma jest liderem w dziedzinie CSR i zrównoważonej logistyki. Innowacyjne praktyki są integralną częścią działalności, a przedsiębiorstwo aktywnie wywiera pozytywny wpływ na cały łańcuch dostaw i otoczenie (ponad 85% surowców zrównoważonych)."
}

# ----------------------------------------------------------------------
# 2. INTERFEJS UŻYTKOWNIKA (Streamlit)
# ----------------------------------------------------------------------

# --- INICJALIZACJA STANU SESJI ---
if 'page' not in st.session_state:
    st.session_state["page"] = "welcome"

if 'wyniki_poziomow' not in st.session_state:
    st.session_state.wyniki_poziomow = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0} 

st.set_page_config(page_title="Narzędzie Oceny CSR w Logistyce", layout="wide") 

initialize_anchor()


# --- LOGIKA PRZECHODZENIA MIĘDZY STRONAMI ---

# 1. STRONA POWITALNA
if st.session_state["page"] == "welcome":
    scroll_to_top() 
    st.title("🌱 Narzędzie Oceny Procesów Logistycznych (CSR)")
    st.header("Witaj w narzędziu do oceny dojrzałości CSR w logistyce!")
    
    st.markdown("""
    To narzędzie zostało stworzone, aby pomóc przedsiębiorstwom logistycznym 
    ocenić aktualny poziom zaangażowania w praktyki zrównoważonego rozwoju (CSR)
    oraz zidentyfikować obszary do poprawy.

    ### Po co ten test?
    1.  **Diagnoza:** Umożliwia szybką ocenę, na którym z 6 Poziomów Dojrzałości 
        (od Poziomu 0: Brak Formalnego CSR, do Poziomu 5: Innowacyjne Przywództwo) 
        znajduje się Twoja firma.

    2.  **Rekomendacje:** Na podstawie odpowiedzi otrzymasz ukierunkowane zalecenia 
        dotyczące kolejnych kroków, które pozwolą przejść na wyższy poziom dojrzałości.

    3.  **Świadomość:** Wzrost świadomości kluczowych aspektów CSR w łańcuchu dostaw.

    Proszę odpowiadać na pytania szczerze i zgodnie z aktualnym stanem w firmie.
    """)
    
    st.button("Rozpocznij Ocenę", on_click=go_to_test)
    
    st.markdown("---")
    st.info("""
    **Narzędzie stworzone na potrzeby pracy inżynierskiej na temat:** *Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR*
    
    **Twórcy testu:** Olga Paszyńska, Justyna Robak, Urszula Sewerniuk
    
    **Promotor pracy:** dr inż. Katarzyna Ragin-Skorecka
    """)


# 2. STRONA Z TESTEM (FORMULARZ)
elif st.session_state["page"] == "test":
    scroll_to_top() 
    st.markdown("Proszę odpowiedzieć na poniższe pytania, aby określić poziom dojrzałości CSR.")
    with st.form("formularz_oceny"):
        
        st.header("Kryteria I: Struktura Organizacyjna i Surowce")
        
        for index, row in pytania_df.iterrows():
            st.subheader(f"{row['Pytanie']}")
            
            opcje_list = list(row['Opcje_Punkty'].keys())
            
            st.radio(
                "Wybierz odpowiedź:", 
                opcje_list, 
                key=row['Klucz'] 
            )

        st.form_submit_button(
            "Oblicz Poziom Zrównoważonego Rozwoju",
            on_click=lambda: (calculate_scores(pytania_df), st.session_state.update(page="results"), scroll_to_top()) 
        )

# 3. STRONA Z WYNIKAMI
elif st.session_state["page"] == "results":
    
    scroll_to_top() # Przewiń do góry, aby zobaczyć wyniki
    st.header("📊 Wynik Oceny i Rekomendacje")
    
    wyniki_poziomow = st.session_state.wyniki_poziomow

    punkty_do_analizy = {p: pkt for p, pkt in wyniki_poziomow.items() if pkt > 0 or p == 0} 
    
    max_punkty_wszystkie = max(punkty_do_analizy.values())
    
    if max_punkty_wszystkie == 0:
        dominujacy_poziom = 0
    else:
        remisowe_poziomy = [p for p, pkt in punkty_do_analizy.items() if pkt == max_punkty_wszystkie]
        dominujacy_poziom = min(remisowe_poziomy)
    
    max_punkty = wyniki_poziomow[dominujacy_poziom]
    
    st.success(f"## 🏆 Osiągnięty Poziom Dojrzałości: {poziomy_nazwy[dominujacy_poziom]}")
    
    # DODANA SEKCJA: WYJAŚNIENIE OSIĄGNIĘTEGO POZIOMU
    st.markdown(f"**Opis:** {poziomy_opisy[dominujacy_poziom]}")

    st.markdown("---")

    # 3. Generowanie Inteligentnego Podsumowania (Wnioski i Rekomendacje)
    st.subheader("Wnioski i Rekomendacje:")
    
    if dominujacy_poziom == 0:
        st.write("Brak formalnych struktur i mierników oraz brak użycia zrównoważonych surowców wskazują na **brak wdrożonego CSR**. Należy jak najszybciej powołać zespół roboczy (Poziom 1).")
    elif dominujacy_poziom == 1:
        st.write("Organizacja wykazuje wstępną świadomość. Rekomendacja: Należy sformalizować działania poprzez wprowadzenie regularnych spotkań zespołu i wyznaczenie celów, aby osiągnąć **Poziom 2 (Transformacja)**.")
    elif dominujacy_poziom == 2:
        st.write("Powołano zespół roboczy. Rekomendacja: Kluczowe jest, aby spotkania zespołu miały **jasno określony cel** (działalność proekologiczna) oraz aby firma zaczęła intensywnie zwiększać użycie **zrównoważonych surowców** (Poziom 3).")
    elif dominujacy_poziom == 3:
        st.write("Prowadzone są regularne spotkania w celu omawiania działań proekologicznych. Rekomendacja: Należy zwiększyć odsetek zrównoważonych surowców do ponad 50% oraz **zintegrować** te cele ze strategią i systemem monitorowania, aby osiągnąć **Poziom 4 (Dojrzałość)**.")
    elif dominujacy_poziom == 4:
        st.write("Zrównoważony rozwój jest częścią strategii. Firma używa dużej ilości zrównoważonych surowców. Rekomendacja: Należy dążyć do **Innowacyjnego Przywództwa (Poziom 5)** poprzez maksymalizację udziału zrównoważonych surowców i współuczestnictwo w sieci dobrych praktyk.")
    elif dominujacy_poziom == 5:
        st.write("Gratulacje! Państwa firma jest innowatorem. Rekomendacja: Kontynuacja działań i wywieranie pozytywnego wpływu na otoczenie.")

    st.markdown("---")

    # 2. Wyświetlenie punktacji w tabeli
    st.subheader("Szczegółowa Punktacja dla Każdego Poziomu:")
    df_wyniki = pd.DataFrame(
        list(wyniki_poziomow.items()), 
        columns=['Poziom', 'Suma Punktów']
    )
    df_wyniki['Nazwa Poziomu'] = df_wyniki['Poziom'].map(poziomy_nazwy)
    df_wyniki = df_wyniki[['Poziom', 'Nazwa Poziomu', 'Suma Punktów']]
    
    # FUNKCJA PODŚWIETLANIA:
    def highlight_dominant_level(row, dominant_level_id):
        is_dominant = row['Poziom'] == dominant_level_id
        return ['background-color: #ffdd44; color: black' if is_dominant else '' for _ in row]
    st.dataframe(
        df_wyniki.style.apply(highlight_dominant_level, 
                              axis=1, # Ważne: stosujemy do wierszy
                              dominant_level_id=dominujacy_poziom),
        hide_index=True
    )

    st.markdown("---")
    
    st.button("Wróć do Pytań / Wykonaj Nową Ocenę", 
              on_click=go_to_test)
    
    # Stopka z podpisami twórców
    st.markdown(f"""
    ***
    <p style='font-size: 10px; text-align: center;'>
        Narzędzie stworzone na potrzeby pracy inżynierskiej pt. "Opracowanie narzędzia oceny procesów logistycznych pod kątem zrównoważonego rozwoju i zasad CSR".<br>
        Autorzy: Olga Paszyńska, Justyna Robak, Urszula Sewerniuk. Promotor: dr inż. Katarzyna Ragin-Skorecka.
    </p>
    """, unsafe_allow_html=True)
