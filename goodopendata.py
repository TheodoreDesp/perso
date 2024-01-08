import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff

# Titre de la page
st.title("L'énergie en France 🔵⚪️🔴")

# Chargement des données
@st.cache_data
def load_data():
    data = pd.read_excel("dataset_electricite_france.xlsx")
    data = data.iloc[1:]  # Ignorer les en-têtes personnalisés

    # Convertir 'Période' en datetime, ajuster le format si nécessaire
    data['Période'] = pd.to_datetime(data['Période'], errors='coerce')

    for col in data.columns[1:]:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    data.dropna(subset=['Période'], inplace=True)  # Supprimer les lignes où 'Période' est NaT
    data.set_index('Période', inplace=True)
    return data

data = load_data()

# Fonction pour la première page
def page1():
    st.title("La production d'énergie en France")

    # Extraction des années uniques présentes dans les données
    years = data.index.year.unique()
    start_year, end_year = st.slider(
        'Sélectionnez la plage d\'années:',
        min_value=int(years.min()),
        max_value=int(years.max()),
        value=(int(years.min()), int(years.max())),
        key='year_range_page1'
    )

    # Après la sélection de la plage d'années, triez les données par 'Période'
    data_filtered = data[(data.index.year >= start_year) & (data.index.year <= end_year)]
    data_filtered.sort_index(inplace=True)  # Assurez-vous que les données sont triées

    # Graphique de la production totale nette d'électricité
    col_name = 'Production totale nette d\'électricité (en GWh)'
    fig_total = px.line(
        data_filtered, 
        x=data_filtered.index, 
        y=col_name, 
        title='Production Totale Nette d\'Électricité en France (en GWh)',
        labels={'Période': 'Date', col_name: 'Production (en GWh)'}
    )
    
    # Ajout d'une courbe de tendance moyenne en rouge
    fig_total.add_scatter(
        x=data_filtered.index, 
        y=data_filtered[col_name].rolling(window=12).mean(), 
        mode='lines', 
        name='Tendance moyenne',
        line=dict(color='red')  # Définir la couleur de la ligne de tendance en rouge
    )

    # Masquer la légende
    fig_total.update_layout(showlegend=False)



    st.plotly_chart(fig_total, use_container_width=True)
    
    st.title("La production en fonction de l'énergie")

    # Aggregation des données mensuelles en moyennes annuelles
    data_annual = data_filtered.resample('Y').mean()  # 'Y' signifie 'fin d'année'

    # Sélectionnez les colonnes à afficher
    columns_to_plot = [
        "Production nette d'électricité nucléaire (en GWh)",
        "Production nette d'électricité hydraulique (en GWh)",
        "Production nette d'électricité éolienne (en GWh)",
        "Production nette d'électricité photovoltaïque (en GWh)",
        "Production nette d'électricité thermique (en GWh)"
    ]

    # Création du graphique Plotly avec les données annuelles agrégées
    fig = go.Figure()
    for col in columns_to_plot:
        fig.add_trace(go.Scatter(x=data_annual.index.year, y=data_annual[col], name=col, mode='lines'))

    # Ajustement de la taille du graphique
    fig.update_layout(
        legend=dict(
            x=0.5,
            xanchor='center',
            y=-0.3,
            yanchor='top',
            orientation='h',
            font=dict(size=16),  # Augmentez la taille de la police ici
            traceorder='normal',
            itemsizing='constant'
        ),
        autosize=False,  # Désactiver l'ajustement automatique de la taille
        width=1000,  # Largeur du graphique en pixels
        height=600,  # Hauteur du graphique en pixels
    )

    # Affichage du graphique dans Streamlit avec les données filtrées
    st.plotly_chart(fig, use_container_width=True)

    st.title("La production et les corrélations")

    # Calculer la variation annuelle pour chaque type de production
    data['variation nucléaire'] = data["Production nette d'électricité nucléaire (en GWh)"].pct_change()
    data['variation éolienne'] = data["Production nette d'électricité éolienne (en GWh)"].pct_change()
    data['variation thermique'] = data["Production nette d'électricité thermique (en GWh)"].pct_change()
    data['variation hydraulique'] = data["Production nette d'électricité hydraulique (en GWh)"].pct_change()
    data['variation photovoltaïque'] = data["Production nette d'électricité photovoltaïque (en GWh)"].pct_change()

    # Supprimer les valeurs NaN dues au calcul de variation
    data_change = data.dropna()

    # Permettre à l'utilisateur de choisir le type d'énergie à comparer avec le nucléaire
    energy_type = st.selectbox(
        "Choisissez le type d'énergie à comparer avec le nucléaire:",
        ('éolienne', 'thermique', 'hydraulique'),
        key='energy_type_selection_page1'
    )

    # Mapper le choix de l'utilisateur à la colonne correspondante
    energy_map = {
        'éolienne': 'variation éolienne',
        'thermique': 'variation thermique',
        'hydraulique': 'variation hydraulique',
    }

    fig = px.scatter(
        data_change,
        x='variation nucléaire',
        y=energy_map[energy_type],
        trendline='ols',
        labels={
            'x': 'Variation annuelle de la production nucléaire (%)',
            'y': f'Variation annuelle de la production {energy_type} (%)'
        },
        title=f"Corrélation entre les variations annuelles de la production nucléaire et {energy_type}"
    )

    # Masquer les points en définissant leur opacité à 0
    fig.update_traces(marker=dict(opacity=0))

    # Afficher le graphique dans Streamlit
    st.plotly_chart(fig, use_container_width=True)

# Fonction pour la deuxième page
def page2():
    st.title("Les exports et imports commerciaux de la France")

    # Charger les données d'exports
    @st.cache_data
    def load_export_data():
        export_data = pd.read_csv("imports-exports-commerciaux.csv", delimiter=';')
        
        # Convertir la colonne 'date' en datetime
        export_data['date'] = pd.to_datetime(export_data['date'], format='%d/%m/%Y', errors='coerce')
        
        # Trier les données par date
        export_data.sort_values('date', inplace=True)
        
        # S'assurer que les données sont numériques et que les séparateurs de milliers soient corrects
        cols_to_convert = export_data.select_dtypes(include=['object']).columns
        export_data[cols_to_convert] = export_data[cols_to_convert].apply(lambda x: x.str.replace('.', '').str.replace(',', '.').astype(float))
        
        return export_data

    export_data = load_export_data()

    # Sélection du pays
    country_codes = {'GB': 'Grande-Bretagne', 'CWE': 'CWE', 'CH': 'Suisse', 'IT': 'Italie', 'ES': 'Espagne'}
    selected_country_code = st.selectbox(
        'Sélectionnez le pays:', 
        list(country_codes.keys()), 
        format_func=lambda x: country_codes[x], 
        key='unique_country_select_page2'
    )

    # Calcul des totaux des exports et imports par année pour le pays sélectionné
    export_data['year'] = export_data['date'].dt.year
    export_col = f'fr_{selected_country_code.lower()}'
    import_col = f'{selected_country_code.lower()}_fr'
    
    # Définir les années minimum et maximum disponibles pour le slider
    min_year = int(export_data['year'].min())
    max_year = int(export_data['year'].max())

    # Sélection d'une plage d'années pour l'affichage avec un slider
    years_to_display = st.slider(
        'Sélectionnez une plage d\'années:', 
        min_year, 
        max_year, 
        (min_year, max_year),
        key='year_range_page2'
    )

    # Filtrer les données pour les années et le pays sélectionnés
    data_filtered = export_data[(export_data['year'] >= years_to_display[0]) & (export_data['year'] <= years_to_display[1])]
    
    # Création des graphiques des exports
    fig_exports = px.bar(
        data_filtered, 
        x='year', 
        y=export_col, 
        labels={'year': 'Année', export_col: 'Exports (en GWh)'},
        title=f'Exports de la France vers {country_codes[selected_country_code]}'
    )
    
    # Afficher les graphiques des exports dans Streamlit
    st.plotly_chart(fig_exports, use_container_width=True)

    # Création des graphiques des imports
    fig_imports = px.bar(
        data_filtered, 
        x='year', 
        y=import_col, 
        labels={'year': 'Année', import_col: 'Imports (en GWh)'},
        title=f'Imports de la France depuis {country_codes[selected_country_code]}'
    )
    
    # Afficher les graphiques des imports dans Streamlit
    st.plotly_chart(fig_imports, use_container_width=True)

    
def page3():
    st.title("KPI")

    # CSS to inject contained in a string
    kpi_style = """
    <style>
    .kpi_box {
        border: 2px solid #8ab4f8;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0px;
        background-color: #1e1f1e;
    }
    .kpi_box h4 {
        margin: 0 0 5px 0;
        font-weight: 500;
        font-size: 1.25em;
        color: #1a73e8;
    }
    .kpi_box p {
        margin: 4px 0;
        font-size: 1.1em;
    }
    .kpi_box b {
        font-weight: 700;
    }
    </style>
    """

    # Inject CSS with Markdown
    st.markdown(kpi_style, unsafe_allow_html=True)

    # Define the ratio of households per GWh
    kpi1_ratio = 220  # Number of households per GWh

    # Production values for 2022 in GWh
    production_nucleaire_2022 = 23000
    production_hydraulique_2022 = 4204
    production_eolien_2022 = 3170  # Assuming the value is in GWh (3170000 MWh)
    production_photovoltaique_2022 = 1600  # Assuming the value is in GWh (1600000 MWh)
    production_thermique_2022 = 5300

    # Calculate the number of households for each production type
    households_nucleaire_2022 = production_nucleaire_2022 * kpi1_ratio
    households_hydraulique_2022 = production_hydraulique_2022 * kpi1_ratio
    households_eolien_2022 = production_eolien_2022 * kpi1_ratio
    households_photovoltaique_2022 = production_photovoltaique_2022 * kpi1_ratio
    households_thermique_2022 = production_thermique_2022 * kpi1_ratio


    # Display KPIs using Markdown and custom styles
    st.markdown(f"""
    <div class="kpi_box">
        <h4>Consommation par foyer</h4>
        <p>1 GWh équivaut à l'énergie consommée par <b>{kpi1_ratio} foyers</b></p>
    </div>
    <div class="kpi_box">
        <h4>Production nucléaire en 2022</h4>
        <p>{production_nucleaire_2022} GWh</p>
        <p><b>{households_nucleaire_2022:,} foyers alimentés</b></p>
    </div>
    <div class="kpi_box">
        <h4>Production hydraulique en 2022</h4>
        <p>{production_hydraulique_2022} GWh</p>
        <p><b>{households_hydraulique_2022:,} foyers alimentés</b></p>
    </div>
    <div class="kpi_box">
        <h4>Production éolienne en 2022</h4>
        <p>{production_eolien_2022} GWh</p>
        <p><b>{households_eolien_2022:,} foyers alimentés</b></p>
    </div>
    <div class="kpi_box">
        <h4>Production photovoltaïque en 2022</h4>
        <p>{production_photovoltaique_2022} GWh</p>
        <p><b>{households_photovoltaique_2022:,} foyers alimentés</b></p>
    </div>
        <div class="kpi_box">
        <h4>Production thermique en 2022</h4>
        <p>{production_thermique_2022} GWh</p>
        <p><b>{households_thermique_2022:,} foyers alimentés</b></p>
    </div>
    """, unsafe_allow_html=True)



# Menu latéral pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choisir une page:", 
    ["La production", "Les exports", "KPI"],  # Add "KPI" to the list of pages
    key='page_navigation'
)

# Appel des fonctions en fonction de la sélection
if page == "La production":
    page1()
elif page == "Les exports":
    page2()
elif page == "KPI":  # This line is new, and it checks if the KPI page is selected
    page3()  # Call the KPI page function if the KPI page is selected


