import pandas as pd
import ftfy
import streamlit as st

def repair_text(text):
    # Sistema potenziali errori nel testo
    if isinstance(text, str):
        return ftfy.fix_text(text)
    return text

def clean_data(df):
    # Cancella le prime 7 righe in quanto inutili
    df = df.iloc[7:].reset_index(drop=True)

    # Cambiamo i nomi delle colonne con la prima riga
    df.columns = df.iloc[0]  # Prendi la prima riga come intestazioni
    df = df[1:].reset_index(drop=True)  # Elimina la riga usata come intestazioni

    # Eliminiamo la colonna Rating
    df = df.drop(columns=["Rating", 8])

    # Eliminiamo i valori vuoti escludendo la colonna "Related Series"
    columns_to_check = [col for col in df.columns if col != "Related Series"]
    df = df.dropna(subset=columns_to_check)

    return df

def extract_set(df, column_name):
    # Estrae un set di valori da una colonna di un dataframe
    result = set()
    for cell in df[column_name].dropna():
        valori = [v.strip() for v in cell.split(",")]
        result.update(valori)
    return sorted(result)

# Funzione in cache per ottimizzare i tempi di esecuzione
@st.cache_data
def produce_data():
    # URL pubblico del foglio Google
    url = "https://docs.google.com/spreadsheets/d/1ZluFOVtJCv-cQLXWhmCLNoZFIMLV0eTrqozwyEb1zw8/htmlview?gid=1182137093"

    # Legge tutte le tabelle HTML visibili nella pagina in encoding utf-8 per i caratteri coreani
    tables = pd.read_html(url, encoding="utf-8")

    # Estraiamo i dati principali
    main_df = clean_data(tables[0])

    # Estraiamo i generi
    genre_df = extract_set(main_df, "Genre(s)")

    # Estraiamo le categorie
    categories_df = extract_set(main_df, "Categories")

    # Estraiamo gli status
    status_df = extract_set(main_df, "Status")

    return main_df, genre_df, categories_df, status_df

# Applica i filtri selezionati dagli utenti alle celle per una lista di valori da controllare
def search_filter(cell, values):
    # Se la lista è vuota o None, accetta tutto
    if not values or values[0] is None:
        return True
    # Ottiene i valori della cella
    cell_values = set(v.strip() for v in cell.split(","))
    # Prendiamo la cella solo se tutti i valori dell'utente sono sottoinsieme della cella
    return set(values).issubset(set(cell_values))

# Mostra in maniera carina le righe
def print_elements(df):
    for row in df.itertuples():
        with st.container():
            st.header(row[1])
            cols = st.columns([0.7,0.3])
            with cols[0]:
                st.subheader("Synopsis")
                st.write(row[2])
                st.write("**Author**: " + row[5] + " (" + row[6] + ")")
            cols = st.columns(4)
            with cols[0]:
                st.subheader("Genres")
                genres = list(g.strip() for g in row[3].split(","))
                st.pills("Genres",genres,disabled=True, key=row[1] + "Genres", label_visibility="hidden")
            with cols[1]:
                st.subheader("Categories")
                categories = list(g.strip() for g in row[4].split(","))
                st.pills("Categories",categories,disabled=True, key=row[1] + "Categories", label_visibility="hidden")
            with cols[2]:
                st.subheader("Status")
                st.text(row[8])
            with cols[3]:
                st.subheader("# Chapters")
                st.text(row[7])
            st.divider()

def page_buttons(total_pages, key):
    # Funzioni per navigare tra le pagine
    def previous_page():
        # Per evitare di andare sui negativi
        if st.session_state.current_page > 1:
            st.session_state.current_page -= 1

    def pagina_successiva():
        # Per evitare di andare sovranumerati
        if st.session_state.current_page < total_pages:
            st.session_state.current_page += 1

    # Layout dei pulsanti
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.button("⬅️ Previous", on_click=previous_page, key=key+"prev")
    with col3:
        st.button("Next ➡️", on_click=pagina_successiva, key=key+"next")
    # Visualizza la pagina corrente del DataFrame
    st.write(f"Page {st.session_state.current_page} of {total_pages}")


if __name__ == "__main__":
    # Inseriamo nel session state la pagina
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    st.title("ManwhaBang")

    # Prendiamo i dati
    main_df, genre_df, categories_df, status_df = produce_data()

    # Stampiamo i filtri
    st.header("Genre")
    genres = st.pills("Genre", genre_df, selection_mode="multi", label_visibility="hidden")
    st.header("Categories")
    categories = st.pills("Categories", categories_df, selection_mode="multi", label_visibility="hidden")
    st.header("Status")
    # N.B. Status è inserito in una lista per far funzionare la maschera
    status = [st.segmented_control("Status", status_df, selection_mode="single", label_visibility="hidden")]

    # Ottiene la maschera da inserire sul dataframe per effettuare la ricerca
    # Applica a ogni cella di ogni colonna interessata la funzione search_filter
    mask = main_df["Genre(s)"].apply(lambda x: search_filter(x, genres)) & \
           main_df["Categories"].apply(lambda x: search_filter(x, categories)) & \
           main_df["Status"].apply(lambda x: search_filter(x, status))

    # Filtra il dataframe
    df_result = main_df[mask]

    # Imposta righe per pagina
    rows_per_page = 20
    # Calcola le pagine totali (-1 alle righe per gestire i casi in cui la divisione non è precisa, +1 alle pagine per lo stesso motivo)
    total_pages = (len(df_result) - 1) // rows_per_page + 1

    # Calcola gli indici per la pagina corrente
    start_index = (st.session_state.current_page - 1) * rows_per_page
    end_index = start_index + rows_per_page

    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1

    page_buttons(total_pages,"1")

    # Mostra gli elementi del dataframe paginati
    print_elements(df_result.iloc[start_index:end_index])

    page_buttons(total_pages,"2")