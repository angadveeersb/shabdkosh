import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Set page configuration
st.set_page_config(
    page_title="ਸ਼ਬਦਕੋਸ਼ - Punjabi Dictionary",
    page_icon="📚",
    layout="centered"
)

# Add Noto Serif Gurmukhi font and styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+Gurmukhi:wght@400;600;700&display=swap');
    
    .stApp {
        font-family: 'Noto Serif Gurmukhi', serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Noto Serif Gurmukhi', serif !important;
    }
    
    .stTextInput > div > div > input {
        font-family: 'Noto Serif Gurmukhi', serif;
    }
    
    .stMarkdown p, .stWrite, .stCaption {
        font-family: 'Noto Serif Gurmukhi', serif;
    }
    
    /* Specific styling for Gurmukhi text */
    [lang="pa"] {
        font-family: 'Noto Serif Gurmukhi', serif;
        font-size: 1.1em;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# Main title
st.title("ਸ਼ਬਦਕੋਸ਼ - Punjabi Dictionary")
st.markdown("---")

def scrape_punjabipedia_definitions(word):
    """
    Scrapes the Punjabipedia page for definitions of a word by
    navigating the HTML structure.
    """
    try:
        # Encode the word for the URL
        encoded_word = urllib.parse.quote(word)
        url = f'https://punjabipedia.org/topic.aspx?txt={encoded_word}'

        # 1. Fetch the content with a User-Agent header
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes

        # 2. Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # 3. Locate the main content area
        # Based on the HTML, 'col-sm-10' is the most specific container
        main_content = soup.find('div', class_='col-sm-10')
        
        # Fallback if the class name changes
        if not main_content:
            main_content = soup.find('div', class_='col-sm-12 main-box')
            if not main_content:
                # Last resort, but less reliable
                main_content = soup.find('body') 
        
        if not main_content:
            return "Could not find the main content container."

        # 4. Find all definition blocks using the <h1> tag as an anchor
        definition_headers = main_content.find_all('h1')
        final_definitions = []

        for h1 in definition_headers:
            source_tag = h1.find('small')
            
            # Find all <p> tags that are siblings after the <h1>
            definition_paragraphs = []
            current_element = h1.find_next_sibling()
            
            # Collect all <p> tags until we hit another <h1> or <hr> or end of content
            while current_element and current_element.name not in ['h1', 'hr']:
                if current_element.name == 'p':
                    # Handle nested <p> tags - find all p tags within this element
                    nested_ps = current_element.find_all('p')
                    if nested_ps:
                        # If there are nested <p> tags, add each one separately
                        for nested_p in nested_ps:
                            definition_paragraphs.append(nested_p)
                    else:
                        # If no nested <p> tags, add the element itself
                        definition_paragraphs.append(current_element)
                current_element = current_element.find_next_sibling()

            # Ensure we found both the source and at least one definition paragraph
            if source_tag and definition_paragraphs:
                
                # Extract and clean the source text
                source_text = source_tag.get_text(strip=True)
                source_text = source_text.replace('ਸਰੋਤ :', '').strip()

                # Process each paragraph separately
                definition_texts = []
                for paragraph in definition_paragraphs:
                    # Extract and clean the definition text for each paragraph
                    definition_text = paragraph.get_text(separator=' ', strip=True)
                    
                    # Remove [ਵਿਸ਼ੇ] or similar bracketed tags
                    definition_text = re.sub(r'\[.*?\]', '', definition_text).strip()
                    
                    # Remove the word itself if it starts the definition
                    definition_text = re.sub(
                        rf'^{re.escape(word)}\s*[\.,—:]?', 
                        '', 
                        definition_text, 
                        flags=re.IGNORECASE
                    ).strip()
                    
                    # Only add non-empty paragraphs (and skip very short ones like just spaces)
                    if definition_text and len(definition_text.strip()) > 1:
                        definition_texts.append(definition_text)

                # Ensure we have non-empty results before adding
                if source_text and definition_texts:
                    final_definitions.append({
                        "Source": source_text,
                        "Definitions": definition_texts  # Changed to plural to store multiple paragraphs
                    })            

        return final_definitions

    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching the page: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Create a text input for word search
st.subheader("Word Search")
word_input = st.text_input(
    "Enter a word in Gurmukhi:",
    placeholder="Type your word here... (ਇੱਥੇ ਆਪਣਾ ਸ਼ਬਦ ਲਿਖੋ...)",
    help="You can enter words in Gurmukhi"
)

# Create columns for better layout
col1, col2 = st.columns([3, 1])

with col2:
    search_button = st.button("Search", type="primary", use_container_width=True)

# Store the input in a variable and display it
if word_input and (search_button or word_input):
    # Store the word in a variable
    searched_word = word_input.strip()
    
    if searched_word:
        # Display the stored word
        st.success(f"Searching for: **{searched_word}**")
        
        # Show loading spinner while fetching definitions
        with st.spinner("🔄 Fetching definitions from Punjabipedia..."):
            definitions = scrape_punjabipedia_definitions(searched_word)
        
        # Display definitions
        if isinstance(definitions, list) and definitions:
            st.markdown("---")
            st.subheader("📖 Definitions")
            
            # Display each definition in a simple container format with border
            for i, definition in enumerate(definitions, 1):
                with st.container(border=True):
                    st.markdown(f"**Definition {i}**")
                    
                    # Display each paragraph as a separate line with spacing
                    for idx, paragraph in enumerate(definition['Definitions']):
                        st.subheader(paragraph)
                    
                    st.caption(f"Source: {definition['Source']}")
                    st.markdown("")  # Add some spacing
        
        elif isinstance(definitions, list) and not definitions:
            st.warning("⚠️ No definitions found for this word. Please try a different word or check the spelling.")
            st.info("💡 **Tip:** Try searching with:\n- Different spellings\n- Simpler forms of the word\n- Related words")
        
        else:
            # Handle error messages
            st.error(f"❌ Error fetching definitions: {definitions}")
            st.info("🔧 **Troubleshooting:**\n- Check your internet connection\n- Try again in a few moments\n- Verify the word spelling")
        
        # Display word information in an expandable section
        with st.expander("ℹ️ Word Information", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Original input:** {word_input}")
                st.write(f"**Cleaned word:** {searched_word}")
            
            with col2:
                st.write(f"**Word length:** {len(searched_word)} characters")
                script_type = 'Gurmukhi (ਗੁਰਮੁਖੀ)' if any(ord(char) >= 0x0A00 and ord(char) <= 0x0A7F for char in searched_word) else 'English/Roman'
                st.write(f"**Script:** {script_type}")

else:
    # Welcome message when no input
    st.info("👆 **Welcome to Punjabi Dictionary!**\n\nEnter a word above to search for its definitions from Punjabipedia.")
    
    

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Built with ❤️ by Angadveer Singh | ਸਤਿਨਾਮ ਵਾਹਿਗੁਰੂ"
    "</div>",
    unsafe_allow_html=True
)