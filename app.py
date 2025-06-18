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
    """Génère le prompt pour GPT à partir du texte du CDC."""
    return f"""
Tu es un assistant expert en conception fonctionnelle de systèmes d'information, et tu dois rédiger un Dossier de Conception Fonctionnelle (DCF) à partir d'un cahier des charges (CDC) fourni ci-dessous.

Le DCF que tu vas rédiger doit **respecter rigoureusement la structure suivante**, issue du guide d'élaboration DDI M IT 02.02 :

---

### 1. CADRE GENERAL
1.1. Présentation générale du système (objectifs, fonctions globales)
1.2. Références (documents applicables et références)
1.3. Environnement (positionnement dans le SI, environnement technique)
1.4. Terminologie et sigles utilisés

### 2. ARCHITECTURE FONCTIONNELLE
2.1. Modules fonctionnels (découpage, description des modules)
2.2. Synoptique fonctionnel (flux entre fonctions)

### 3. SPECIFICATIONS FONCTIONNELLES
Pour chaque module identifié :
- Nom du module
- Pour chaque fonction :
  - Définition (objectif de la fonction)
  - Identification (code, acteur, déclencheur, conséquences IHM et traitement)
  - Description du processus :
    - Entrées
    - Traitement
    - Sorties
    - Règles de gestion (Pas d'Abréviation écrit la règle de gestion)

### 4. REPRISE DE L'EXISTANT
4.1. Procédure de reprise
4.2. Contraintes de reprise

### 5. RECAPITULATIF DES REGLES DE GESTION
Tableau récapitulatif avec fonction associée à chaque règle.

### 6. VISA DE VALIDATION
Présentation des aspects validés et les parties prenantes concernées.

---

Tu dois **extraire, analyser et structurer le contenu du CDC suivant** pour produire automatiquement un DCF de qualité conforme à cette structure, en tenant compte :
- des besoins exprimés,
- des règles de gestion métier,
- des exigences fonctionnelles,
- des contraintes techniques,
- des modules évoqués.

Voici le contenu du CDC :

\"\"\"{cdc_text[:15000]}\"\"\"

Rédige maintenant un DCF complet et bien formaté à partir de ce CDC.
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