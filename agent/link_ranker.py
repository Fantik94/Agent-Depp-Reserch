import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import io
import csv

def display_ranked_links(result):
    """Affiche les liens classés par pertinence avec détails"""
    st.markdown("### 🔗 Liens trouvés classés par pertinence")
    
    if not result.get('search_results'):
        st.warning("Aucun lien trouvé")
        return
    
    # Classifier les liens par pertinence
    ranked_links = rank_links_by_relevance(result['search_results'], result.get('user_query', ''))
    
    # Afficher les statistiques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔗 Total liens", len(ranked_links))
    with col2:
        e_commerce_count = sum(1 for link in ranked_links if is_ecommerce_link(link['url']))
        st.metric("🛒 Sites e-commerce", e_commerce_count)
    with col3:
        amazon_count = sum(1 for link in ranked_links if 'amazon' in link['url'].lower())
        st.metric("📦 Amazon", amazon_count)
    
    # Affichage des liens classés
    st.markdown("#### 🏆 Classement des résultats (du meilleur au moins bon)")
    
    for i, link in enumerate(ranked_links, 1):
        # Calculer le score de pertinence
        relevance_score = calculate_relevance_score(link, result.get('user_query', ''))
        
        # Déterminer les badges
        badges = get_link_badges(link['url'])
        
        # Créer une carte pour chaque lien
        with st.container():
            # En-tête avec rang et score
            col_rank, col_content = st.columns([1, 9])
            
            with col_rank:
                # Médaille pour les 3 premiers
                if i == 1:
                    st.markdown("# 🥇")
                elif i == 2:
                    st.markdown("# 🥈")
                elif i == 3:
                    st.markdown("# 🥉")
                else:
                    st.markdown(f"## #{i}")
            
            with col_content:
                # Titre avec lien cliquable
                st.markdown(f"**[{link['title']}]({link['url']})**")
                
                # Badges
                badge_html = " ".join([f'<span style="background: {color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin-right: 4px;">{text}</span>' 
                                     for text, color in badges])
                if badge_html:
                    st.markdown(badge_html, unsafe_allow_html=True)
                
                # Description/snippet
                if link.get('snippet'):
                    st.write(f"📝 {link['snippet'][:200]}{'...' if len(link['snippet']) > 200 else ''}")
                
                # Informations techniques
                col_tech1, col_tech2, col_tech3 = st.columns(3)
                with col_tech1:
                    st.caption(f"⭐ Score: {relevance_score:.1f}/10")
                with col_tech2:
                    domain = extract_domain(link['url'])
                    st.caption(f"🌐 {domain}")
                with col_tech3:
                    st.caption(f"🔍 Via {link.get('source', 'N/A')}")
        
        st.markdown("---")
    
    # Actions sur les liens
    st.markdown("#### 💾 Actions")
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("📋 Copier le top 5", help="Copier les 5 meilleurs liens"):
            top_5_text = create_top_links_text(ranked_links[:5])
            st.code(top_5_text)
    
    with col_action2:
        if st.button("📄 Exporter CSV", help="Télécharger au format CSV"):
            csv_data = create_csv_export(ranked_links)
            st.download_button(
                label="💾 Télécharger",
                data=csv_data,
                file_name="liens_classes.csv",
                mime="text/csv"
            )
    
    with col_action3:
        if st.button("🔗 URLs uniquement", help="Liste simple des URLs"):
            urls_text = "\n".join([link['url'] for link in ranked_links[:10]])
            st.code(urls_text)

def rank_links_by_relevance(links, query):
    """Classe les liens par pertinence"""
    scored_links = []
    
    for link in links:
        score = calculate_relevance_score(link, query)
        scored_links.append({**link, 'relevance_score': score})
    
    # Trier par score décroissant
    return sorted(scored_links, key=lambda x: x['relevance_score'], reverse=True)

def calculate_relevance_score(link, query):
    """Calcule un score de pertinence pour un lien"""
    score = 0
    query_words = query.lower().split()
    
    title = link.get('title', '').lower()
    snippet = link.get('snippet', '').lower()
    url = link.get('url', '').lower()
    
    # Points pour les mots de la requête dans le titre (poids fort)
    for word in query_words:
        if word in title:
            score += 3
        if word in snippet:
            score += 2
        if word in url:
            score += 1
    
    # Bonus pour sites e-commerce si c'est une recherche produit
    if is_product_query(query) and is_ecommerce_link(url):
        score += 2
    
    # Bonus spécial Amazon
    if 'amazon' in url:
        score += 1.5
    
    # Bonus pour les sites populaires
    popular_domains = ['amazon.fr', 'amazon.com', 'leboncoin.fr', 'fnac.com', 'darty.com', 'boulanger.com']
    domain = extract_domain(url)
    if domain in popular_domains:
        score += 1
    
    # Malus pour les liens trop courts (peu d'info)
    if len(snippet) < 50:
        score -= 0.5
    
    return max(0, score)  # Score minimum 0

def is_product_query(query):
    """Détecte si c'est une recherche de produit"""
    product_keywords = ['meilleur', 'acheter', 'prix', 'pas cher', 'promo', 'solde', 'euro', '€', 'test', 'avis', 'comparatif']
    return any(keyword in query.lower() for keyword in product_keywords)

def is_ecommerce_link(url):
    """Détecte si c'est un site e-commerce"""
    ecommerce_domains = ['amazon', 'fnac', 'darty', 'boulanger', 'cdiscount', 'leboncoin', 'rakuten', 'zalando', 'decathlon']
    return any(domain in url.lower() for domain in ecommerce_domains)

def extract_domain(url):
    """Extrait le domaine d'une URL"""
    try:
        return urlparse(url).netloc.replace('www.', '')
    except:
        return url.split('/')[2] if '/' in url else url

def get_link_badges(url):
    """Retourne les badges appropriés pour un lien"""
    badges = []
    url_lower = url.lower()
    
    if 'amazon' in url_lower:
        badges.append(("AMAZON", "#ff9900"))
    elif any(shop in url_lower for shop in ['fnac', 'darty', 'boulanger']):
        badges.append(("E-COMMERCE", "#007bff"))
    elif 'leboncoin' in url_lower:
        badges.append(("OCCASION", "#28a745"))
    
    if any(word in url_lower for word in ['test', 'review', 'avis']):
        badges.append(("AVIS", "#6f42c1"))
    
    if any(word in url_lower for word in ['promo', 'solde', 'reduction']):
        badges.append(("PROMO", "#dc3545"))
    
    return badges

def create_top_links_text(links):
    """Crée un texte formaté avec les meilleurs liens"""
    text = "🏆 TOP LIENS TROUVÉS\n" + "="*50 + "\n\n"
    
    for i, link in enumerate(links, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {link['title']}\n"
        text += f"   🔗 {link['url']}\n"
        if link.get('snippet'):
            text += f"   📝 {link['snippet'][:100]}...\n"
        text += "\n"
    
    return text

def create_csv_export(links):
    """Crée un export CSV des liens"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['Rang', 'Titre', 'URL', 'Domaine', 'Score', 'Snippet', 'Source'])
    
    # Données
    for i, link in enumerate(links, 1):
        writer.writerow([
            i,
            link['title'],
            link['url'],
            extract_domain(link['url']),
            f"{link.get('relevance_score', 0):.1f}",
            link.get('snippet', '')[:200],
            link.get('source', 'N/A')
        ])
    
    return output.getvalue() 