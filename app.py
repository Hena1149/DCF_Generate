import streamlit as st
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from docx import Document
from openai import AzureOpenAI
import io
import time

# Configuration de la page
st.set_page_config(
    page_title="Générateur de DCF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le thème sombre élégant
st.markdown("""
<style>
    :root {
        --primary-color: #1a1a1a;
        --secondary-color: #2a2a2a;
        --text-color: #ffffff;
        --accent-color: #4a8cff;
    }
    
    .stApp {
        background-color: var(--primary-color);
        color: var(--text-color);
    }
    
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>select,
    .stFileUploader>div>div {
        background-color: var(--secondary-color) !important;
        color: var(--text-color) !important;
        border: 1px solid #444 !important;
    }
    
    .stButton>button {
        background-color: var(--accent-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 8px 16px !important;
    }
    
    .stButton>button:hover {
        background-color: #3a7cdf !important;
    }
    
    .sidebar .sidebar-content {
        background-color: var(--secondary-color) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color) !important;
    }
    
    .stProgress>div>div>div>div {
        background-color: var(--accent-color) !important;
    }
    
    .stMarkdown {
        color: var(--text-color) !important;
    }
    
    .stAlert {
        background-color: var(--secondary-color) !important;
    }
</style>
""", unsafe_allow_html=True)

def read_file(uploaded_file):
    """Lit le contenu d'un fichier PDF, TXT ou DOCX."""
    if uploaded_file.type == "application/pdf":
        text = ""
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    
    elif uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8")
    
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = DocxDocument(io.BytesIO(uploaded_file.read()))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    else:
        raise ValueError("Format non supporté. Utilisez un fichier PDF, TXT ou DOCX.")

def generate_prompt(cdc_text):
    """Génère le prompt pour GPT à partir du texte du CDC"""
    return f"""
Tu es un assistant expert en conception fonctionnelle de systèmes d'information, et tu dois rédiger un Dossier de Conception Fonctionnelle (DCF) détaillé et complet à partir d'un cahier des charges (CDC) fourni ci-dessous.

Le DCF que tu vas rédiger doit **respecter rigoureusement la structure suivante**, issue du guide d'élaboration DDI M IT 02.02, en fournissant des informations précises et exhaustives pour chaque section :

---

### 1. CADRE GENERAL
1.1. Présentation générale du système
   - Objectifs stratégiques et opérationnels
   - Périmètre fonctionnel précis
   - Finalité du système
   - Bénéfices attendus
   - Publics cibles

1.2. Références
   - Documents normatifs (liste complète)
   - Standards applicables
   - Contraintes réglementaires
   - Références aux documents projets

1.3. Environnement
   - Architecture technique détaillée
   - Systèmes connectés (interfaces)
   - Contraintes d'intégration
   - Prérequis matériels/logiciels
   - Environnement de déploiement

1.4. Terminologie et sigles
   - Glossaire complet avec définitions
   - Liste des acronymes avec explications
   - Termes techniques spécifiques

### 2. ARCHITECTURE FONCTIONNELLE
2.1. Modules fonctionnels
   - Découpage modulaire détaillé
   - Responsabilités de chaque module
   - Interactions entre modules
   - Spécificités techniques

2.2. Synoptique fonctionnel
   - Diagramme textuel des flux
   - Séquencement des opérations
   - Points d'intégration critiques
   - Flux principaux et secondaires

### 3. SPECIFICATIONS FONCTIONNELLES (À DÉTAILLER POUR CHAQUE MODULE)
Pour chaque module identifié :
- Nom du module et version
- Description approfondie :
  * Finalité et portée
  * Contraintes spécifiques
  * Hypothèses techniques

Pour chaque fonction :
  - Définition complète :
    * Objectif métier
    * Valeur ajoutée
    * Critères de succès

  - Identification précise :
    * Code unique (norme de nommage)
    * Acteurs concernés (rôles)
    * Déclencheurs (événements)
    * Préconditions et postconditions
    * Impacts IHM détaillés

  - Description du processus :
    * Entrées : format, source, validation
    * Traitement : algorithme, logique métier
    * Sorties : format, destination, qualité
    * Règles de gestion : formulation complète sans abréviation
    * Cas d'erreur et gestion des exceptions
    * Contrôles de qualité

### 4. REPRISE DE L'EXISTANT
4.1. Procédure de reprise
   - Stratégie de migration
   - Plan de conversion
   - Nettoyage des données
   - Validation post-migration

4.2. Contraintes de reprise
   - Compatibilités
   - Anomalies connues
   - Limitations techniques
   - Périmètre exclu

### 5. RECAPITULATIF DES REGLES DE GESTION
Tableau structuré contenant :
- Identifiant unique de la règle
- Libellé complet et non ambigu
- Module/fonction associée
- Source métier
- Critère d'application
- Exemples concrets
- Exceptions éventuelles

### 6. VISA DE VALIDATION
- Liste des validations requises
- Responsables par domaine
- Critères d'acceptation
- Preuves de validation
- Planning de recette

---

**Directives spécifiques :**
1. Analyse minutieusement le CDC pour extraire toutes les exigences implicites et explicites
2. Structure le contenu de manière logique et progressive
3. Utilise un langage technique précis mais accessible
4. Fournis des exemples concrets quand nécessaire
5. Identifie clairement les dépendances entre composants
6. Mentionne les contraintes et limitations de manière transparente
7. Propose des recommandations pour les aspects critiques

**Approche rédactionnelle :**
- Style professionnel et normatif
- Phrases complètes et structurées
- Terminologie cohérente
- Numérotation précise des éléments
- Mise en forme claire avec des paragraphes aérés

Voici le contenu du CDC à analyser :

\"\"\"{cdc_text[:30000]}\"\"\"

Génère maintenant un DCF exhaustif, en développant particulièrement :
- Les règles de gestion avec leur logique complète
- Les scénarios d'utilisation typiques
- Les cas limites à prendre en compte
- Les interfaces système détaillées
- Les contraintes de performance
"""


def call_gpt(prompt, api_key, endpoint, deployment):
    """Appelle l'API Azure OpenAI pour générer le DCF."""
    client = AzureOpenAI(
        api_key=api_key,
        api_version="2024-02-15-preview",
        azure_endpoint=endpoint
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Tu es un expert en conception de systèmes logiciels."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

def save_dcf_to_word(text, filename="DCF_Généré.docx"):
    """Sauvegarde le texte généré dans un fichier Word."""
    doc = Document()
    for line in text.split('\n'):
        if line.strip() == "":
            continue
        if line.strip().startswith('#') or line.strip().startswith("1.") or line.strip().startswith("2.") or line.strip().startswith("3."):
            doc.add_heading(line.strip(), level=1)
        else:
            doc.add_paragraph(line.strip())
    
    # Sauvegarde en mémoire
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def save_dcf_to_txt(text, filename="DCF_Généré.txt"):
    """Sauvegarde le texte généré dans un fichier texte."""
    buffer = io.StringIO()
    buffer.write(text)
    buffer.seek(0)
    return buffer

def main():
    """Fonction principale de l'application Streamlit."""
    st.title("📄 Générateur de Dossier de Conception Fonctionnelle (DCF)")
    st.markdown("""
    Cette application vous permet de générer automatiquement un Dossier de Conception Fonctionnelle (DCF) à partir d'un cahier des charges (CDC).
    """)
    
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Clé API Azure OpenAI", type="password", help="La clé API pour accéder au service Azure OpenAI")
        endpoint = st.text_input("Endpoint Azure OpenAI", value="https://chat-genai.openai.azure.com/", help="L'URL du endpoint Azure OpenAI")
        deployment = st.text_input("Modèle de déploiement", value="gpt-4o", help="Le nom du modèle déployé dans Azure OpenAI")
        
        st.markdown("---")
        st.info("""
        **Instructions:**
        1. Configurez vos paramètres Azure OpenAI
        2. Téléversez votre fichier CDC (PDF, TXT ou DOCX)
        3. Cliquez sur 'Générer le DCF'
        4. Téléchargez le résultat
        """)
    
    uploaded_file = st.file_uploader(
        "Téléversez votre Cahier des Charges (CDC)",
        type=["pdf", "txt", "docx"],
        help="Format acceptés: PDF, TXT ou DOCX"
    )
    
    if st.button("Générer le DCF", use_container_width=True):
        if not uploaded_file:
            st.error("Veuillez téléverser un fichier CDC.")
            return
        
        if not api_key or not endpoint or not deployment:
            st.error("Veuillez configurer les paramètres Azure OpenAI dans la barre latérale.")
            return
        
        try:
            with st.spinner("Lecture du fichier..."):
                cdc_text = read_file(uploaded_file)
            
            if not cdc_text.strip():
                st.error("Le fichier semble vide ou n'a pas pu être lu correctement.")
                return
            
            with st.spinner("Génération du prompt..."):
                prompt = generate_prompt(cdc_text)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for percent in range(0, 101, 10):
                status_text.text(f"Génération en cours... {percent}%")
                progress_bar.progress(percent)
                time.sleep(0.1)
            
            dcf_result = call_gpt(prompt, api_key, endpoint, deployment)
            
            progress_bar.progress(100)
            status_text.text("Génération terminée!")
            time.sleep(0.5)
            
            st.success("DCF généré avec succès!")
            
            # Affichage du résultat avec un expander
            with st.expander("Aperçu du DCF généré", expanded=False):
                st.text_area("Contenu du DCF", dcf_result, height=400)
            
            # Boutons de téléchargement
            col1, col2 = st.columns(2)
            
            with col1:
                word_buffer = save_dcf_to_word(dcf_result)
                st.download_button(
                    label="📝 Télécharger en Word",
                    data=word_buffer,
                    file_name="DCF_Généré.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            
            with col2:
                txt_buffer = save_dcf_to_txt(dcf_result)
                st.download_button(
                    label="📄 Télécharger en TXT",
                    data=txt_buffer.getvalue().encode("utf-8"),
                    file_name="DCF_Généré.txt",
                    mime="text/plain"
                )
            
        except Exception as e:
            st.error(f"Une erreur est survenue: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()