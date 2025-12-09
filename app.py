# app.py - Narzędzie Oceny CSR w Logistyce wersja 5.6 (Finalne usunięcie kolumny roboczej Qualified)

import streamlit as st
import pandas as pd
import time
import uuid 
import json

# ----------------------------------------------------------------------
# 0. FUNKCJE POMOCNICZE
# ----------------------------------------------------------------------

# Definicja potencjału: maksymalna liczba punktów, jaką można zdobyć dla danego poziomu
# Potencjały są kluczowe dla obliczeń Composite Score
poziom_potencjal = {
    0: 0, # Poziom 0 wyłączony z oceny procentowej
    1: 4, # Max 4 punkty (Q1-Nie, Q2-Nie, Q3-Nie, Q4-1%)
    2: 3, # Max 3 punkty (Q1-Tak, Q2-Tak, Q4-10%)
    3: 2, # Max 2 punkty (Q3-Tak, Q4-30%)
    4: 1, # Max 1 punkt (Q4-50%)
    5: 1  # Max 1 punkt (Q4-85%)
}

# STAŁE DLA SYSTEMU OCENY CSR
CSR_SYSTEM_CONSTANTS = {
    "prior": 0.5,           # Wartość oczekiwana (E)
    "m": 3,                 # Siła wygładzania (m - liczba 'pseudo-obserwacji')
    "alpha": 0.7,           # Waga procentu realizacji (alpha) w wyniku złożonym
    "min_points_fraction": 0.1 # Minimalny procent maksymalnych punktów wymagany do kwalifikacji
}


# FUNKCJA IMPLEMENTUJĄCA SYSTEM OCENY CSR (Composite Score i Kwalifikacja)
def calculate_scores_and_determine_level(pytania_df):
    
    CONST = CSR_SYSTEM_CONSTANTS
    
    # 1. Zliczanie punktów i wstępna weryfikacja
    st.session_state.wyniki_poziomow = {p: 0 for p in poziom_potencjal.keys()} 
    
    all_answered = True
    total_max_score = sum(poziom_potencjal.values())
    
    for index, row in pytania_df.iterrows():
        klucz_pytania = row['Klucz']
        wybrana_opcja_label = st.session_state.get(klucz_pytania)

        if wybrana_opcja_label is None:
            all_answered = False
            break 

        punkty_za_odpowiedz_id = row['Opcje_Punkty'][wybrana_opcja_label]
        przypisane_poziomy = row['Przypisanie_Poziomów'][punkty_za_odpowiedz_id]
        
        # Zliczanie punktów (obsługa starej struktury V4.2)
        poziomy_do_zliczenia = []
        if isinstance(przypisane_poziomy, list):
            poziomy_do_zliczenia = przypisane_poziomy
        elif isinstance(przypisane_poziomy, int):
             poziomy_do_zliczenia = [przypisane_poziomy]
        
        for poziom in poziomy_do_zliczenia:
            if poziom in st.session_state.wyniki_poziomow:
                st.session_state.wyniki_poziomow[poziom] += 1
                
    if not all_answered:
        st.error("Proszę odpowiedzieć na wszystkie pytania, aby obliczyć poziom dojrzałości CSR.")
        return

    # --- 2. IMPLEMENTACJA LOGIKI OCENY (Composite Score) ---
    wyniki_poziomow = st.session_state.wyniki_poziomow
    detailed_results = {}
    
    # Przetwarzanie i obliczenia dla każdego poziomu > 0
    for level, score in wyniki_poziomow.items():
        if level == 0:
            continue
            
        max_p = poziom_potencjal.get(level, 0)
        
        if max_p == 0:
            continue 
            
        # 2.1. Procent realizacji poziomu (surowy)
        pct = score / max_p
        
        # 2.2. Wygładzony procent realizacji (Laplace / Bayesian smoothing)
        adj_pct = (score + CONST['m'] * CONST['prior']) / (max_p + CONST['m'])
        
        # 2.3. Udział poziomu w całej puli pytań (skala poziomu)
        share = score / total_max_score
        
        # 2.4. Wynik złożony (composite score)
        composite = CONST['alpha'] * adj_pct + (1 - CONST['alpha']) * share
        
        # 3.1. Minimalna liczba punktów do kwalifikacji
        # Używamy max(1, ...) aby uniknąć problemów dla max_p = 1
        min_required = max(1, CONST['min_points_fraction'] * max_p) 
        
        # 3.2. Reguła kwalifikacji
        qualified = score >= min_required
        
        detailed_results[level] = {
            "score": score,
            "max_points": max_p,
            "pct": pct,
            "composite": composite, # Zachowujemy Composite Score do sortowania
            "qualified": qualified
        }
        
    # 4. Wyznaczenie poziomu użytkownika
    
    # 4.1. Filtracja i sortowanie
    qualified_levels = [
        (level, data['composite']) 
        for level, data in detailed_results.items() 
        if data['qualified']
    ]
    
    # Sortowanie malejąco wg composite score
    qualified_levels.sort(key=lambda item: item[1], reverse=True)
    
    main_level = 0 # Domyślnie Poziom 0
    secondary_level = 0
    
    if qualified_levels:
        # Główny poziom: ten z najwyższym composite score spośród kwalifikowanych
        main_level = qualified_levels[0][0]
        
        # Drugi najlepszy poziom (jeśli istnieje)
        if len(qualified_levels) > 1:
            secondary_level = qualified_levels[1][0]
    
    # Jeśli żaden poziom nie jest kwalifikowany, poziomem głównym jest Poziom 0
    # (main_level = 0 jest już ustawione jako domyślne)
        
    st.session_state.dominujacy_poziom = main_level
    st.session_state.secondary_level = secondary_level
    st.session_state.detailed_results = detailed_results # Zachowujemy szczegóły dla ewentualnej prostej tabeli
    
    # Uproszczona realizacja procentowa do wyświetlenia
    realizacja_procentowa = {
        lvl: data['pct'] * 100
        for lvl, data in detailed_results.items()
    }
    realizacja_procentowa[0] = 0.0
    st.session_state.realizacja_procentowa = realizacja_procentowa

    # Przejście do strony wyników
    st.session_state.update(page="results")

                
def go_to_test():
    st.session_state["page"] = "test"
    st.session_state.wyniki_poziomow = {p: 0 for p in poziom_potencjal.keys()}
    st.session_state.secondary_level = 0
    st.session_state.detailed_results = {}
    # Resetowanie wszystkich odpowiedzi z formularza przed nowym testem
    for index, row in pytania_df.iterrows():
        if row['Klucz'] in st.session_state:
            st.session_state.pop(row['Klucz'])


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
    
    # Stara struktura, którą musimy zachować
    'Przypisanie_Poziomów': [
        {2: 2, 1: 1}, # 2->P2, 1->P1
        {2: 2, 1: 1}, # 2->P2, 1->P1
        {3: 3, 1: 1}, # 3->P3, 1->P1
        {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5} # 0->P0, 1->P1...
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
    st.session_state.wyniki_poziomow = {p: 0 for p in poziom_potencjal.keys()} 
if 'dominujacy_poziom' not in st.session_state:
    st.session_state.dominujacy_poziom = 0
if 'secondary_level' not in st.session_state:
    st.session_state.secondary_level = 0
if 'realizacja_procentowa' not in st.session_state:
    st.session_state.realizacja_procentowa = {p: 0.0 for p in poziom_potencjal.keys()}
if 'detailed_results' not in st.session_state:
     st.session_state.detailed_results = {}


st.set_page_config(page_title="Narzędzie Oceny CSR w Logistyce", layout="wide") 


# --- LOGIKA PRZECHODZENIA MIĘDZY STRONAMI ---

# 1. STRONA POWITALNA
if st.session_state["page"] == "welcome":
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

    3.  **Edukacja:** Pogłębisz wiedze na temat kluczowych standardów i najlepszych praktyk CSR w Twoim łańcuchu dostaw.
 
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
    with st.form("formularz_oceny"):
        
        st.header("Kryteria I: Struktura Organizacyjna i Surowce")
        
        for index, row in pytania_df.iterrows():
            st.subheader(f"{row['Pytanie']}")
            
            opcje_list = list(row['Opcje_Punkty'].keys())
            
            # Wymuszenie wyboru bez domyślnej opcji
            st.radio(
                "Wybierz odpowiedź:", 
                opcje_list, 
                key=row['Klucz'],
                index=None # Wymuszenie braku wyboru na start
            )

        st.form_submit_button(
            "Oblicz Poziom Zrównoważonego Rozwoju",
            on_click=lambda: (calculate_scores_and_determine_level(pytania_df))
        )

# 3. STRONA Z WYNIKAMI
elif st.session_state["page"] == "results":
    
    st.header("Wynik Oceny i Rekomendacje")
    
    dominujacy_poziom = st.session_state.dominujacy_poziom
    secondary_level = st.session_state.secondary_level
    
    st.success(f"Osiągnięty Poziom Dojrzałości: {poziomy_nazwy[dominujacy_poziom]}")
    
    st.markdown(f"**Opis:** {poziomy_opisy[dominujacy_poziom]}")

    # Sekcja dla poziomu wtórnego - tylko jeśli nie jest Poziomem 0 i jest różny od głównego
    if secondary_level > 0 and secondary_level != dominujacy_poziom:
         st.markdown(f"Firma wykazała również silne dopasowanie do **{poziomy_nazwy[secondary_level]}**.")

    st.markdown("---")

    # 3. Generowanie Wniosków i Rekomendacji
    st.subheader("Wnioski i Rekomendacje:")
    
    if dominujacy_poziom == 0:
        st.write("Brak kwalifikacji do wyższego poziomu. Należy jak najszybciej powołać zespół roboczy (Poziom 1).")
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

    # 2. Wyświetlenie prostej tabeli punktacji
    st.subheader("Punktacja Poziomu:")
    
    realizacje_data = []

    # Generowanie danych tylko dla poziomów 1-5
    for p in sorted(poziom_potencjal.keys()):
        if p == 0: continue
        
        # Pobieranie danych z wyników
        data = st.session_state.detailed_results.get(p, {})
        score = data.get('score', 0)
        max_p = data.get('max_points', poziom_potencjal.get(p, 0))
        pct = data.get('pct', 0.0)
        qualified = data.get('qualified', False)

        realizacje_data.append({
            'Poziom': p,
            'Nazwa Poziomu': poziomy_nazwy[p].split('(')[0].strip(),
            'Max Punkty': max_p,
            'Zdobyte Punkty': score,
        })

    df_wyniki = pd.DataFrame(realizacje_data)
    
    # FUNKCJA PODŚWIETLANIA: Wyróżnia TYLKO główny poziom na żółto
    def highlight_level_status(row, dominant_level_id):
        # Inicjalizacja pustych stylów dla wszystkich kolumn
        styles = ['' for _ in row]
        
        is_dominant = row['Poziom'] == dominant_level_id
        
        # Wyróżnienie głównego, dominującego poziomu (cały wiersz na żółto)
        if is_dominant:
            # Stosujemy styl do wszystkich komórek w wierszu
            return ['background-color: #ffdd44; color: black; font-weight: bold' for _ in row]

        # W przeciwnym razie zwracamy puste style (brak podświetlenia)
        return styles
        
    # Tworzenie stylera w jednym, poprawnie sformatowanym wywołaniu łańcuchowym
    styler = (
        df_wyniki.style
        .apply(highlight_level_status, 
                  axis=1, 
                  dominant_level_id=dominujacy_poziom)
        # POPRAWKA: Dodanie _Qualified do listy kolumn do ukrycia
        .hide(subset=['Poziom'], axis="columns")
    )

    st.dataframe(
        styler,
        hide_index=True,
        use_container_width=True
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
