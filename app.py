# Import modules
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import openai
import re
import random


# Define a function to parse a long string of words to a list of words
def create_lst_words(input_string):
    # Use regex to split the string
    words_list = re.split(r"[,\s\n]+", input_string)

    # To avoid empty strings
    words_list = [word for word in words_list if word]
    return words_list


# Check the defintion and example sentences for a word
def check_word(word, openai_api_key):
    # Innitiate the LLM
    llm = ChatOpenAI(
        openai_api_key=openai_api_key,
        model_name="gpt-3.5-turbo",
        temperature=0)
    
    # Define the prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("user", "{input}")
    ])

    # Add an output parser
    output_parser = StrOutputParser()

    # Define the chain
    chain = prompt | llm | output_parser

    # Define the query
    query = f"""
    Provide the definition and 2 example sentences for the following word: {word}.\n
    **Example Format (word: ocean):**
    Ocean\n
    A vast body of saltwater that covers a large part of the Earth's surface.\n
    The ocean is home to a diverse range of marine life, from tiny plankton to massive whales.\n
    The sound of waves crashing against the shore is a soothing reminder of the power and beauty of the ocean.\n
    """

    # Invoke the chain
    return chain.invoke({'input': query})


# Define a function to pronounce sentences
def pronounce_word(sentences, openai_api_key):
    # Build an OpenAI client
    client = openai.Client(api_key=openai_api_key)

    # Use the OpenAI client to get the pronunciation
    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=sentences) as response:
        response.stream_to_file("sentences.wav")


# Set the page configuration
st.set_page_config(
    page_title="Spelling Bee Master",
    page_icon=":books:",
    layout="centered",
    initial_sidebar_state="auto")


# Define the main function
def main():
    # Set the title
    title_template = """
<div style="background-color: black; padding: 8px;">
<h1 style="color: white; text-align: center;">Spelling Bee Web App</h1>
</div>
"""
    st.markdown(title_template, unsafe_allow_html=True)

    # Set the sidebar with an image
    image_path = "spelling_bee.jpg"
    st.sidebar.image(image_path, use_column_width=True)

    # Add a dropdown menu to the sidebar
    activities = ['Provide Word List', 'Exercise']
    choice = st.sidebar.selectbox("Menu", activities)

    # Choose an activity
    if choice == 'Provide Word List':
        # Provide a text area for user input
        input_words = st.text_area("Enter your word list seperated by comma here: ")
    
        # Add a submit button
        submitted = st.button("Submit")
    
        # Check to make sure that the submit button is clicked and the text area is not empty
        if submitted and input_words:
            # Call function to create a list of words from the input
            word_list = create_lst_words(input_words)
    
            # Save the list in session state
            st.session_state.word_list = word_list
    
    if choice == 'Exercise':
        st.subheader("Listin to the definition and example sentences of a word")

        # Add an OpenAI API key
        openai_api_key = st.secrets['openai_api_key']

        # In the exercise tab, we retrieve the list of words from the session state
        if "word_list" in st.session_state:
            words = st.session_state.word_list
        else:
            st.write("No word list provided. Please submit a word list.")
        
        # Initiate or reset the input key and correct spelling at approporate times
        if "input_key" not in st.session_state:
            st.session_state.input_key = 0
        
        # Innitiate the session state for correct spelling
        if "correct_spelling" not in st.session_state:
            st.session_state.correct_spelling = False
        
        # Select a new word if the previous word was spelled correctly or if it is the first attempt
        if 'word_selected' not in st.session_state or st.session_state.correct_spelling:
            # Check if there is any word left in the list
            if words:
                # Select a random word from the list
                word_index = random.randrange(len(words))
                st.session_state.word_selected = words[word_index]
                # Remove the selected word from the list
                words.pop(word_index)
                # Reset the flag for new word
                st.session_state.correct_spelling = False
            else:
                st.success("Congratulations! You have spelled all words correctly.")
                # Exit the function to prevent further execution
                return
            
        # Call the function to check the word and provide the definition and example sentences
        word_selected = st.session_state.word_selected
        response = check_word(word_selected, openai_api_key)

        # Call the function to pronounce the word and sentences
        pronounce_word(response, openai_api_key)
        audio_file = open("sentences.wav", "rb")
        audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/wav")

        # Ask the user to spell the word
        word_spelled = st.text_input("Spell the word", key=f"spell_input_{st.session_state.input_key}")

        # Check button and spelling logic
        check_button = st.button("Check Spelling")
        if check_button:
            # If spelling is correct:
            if word_spelled.lower() == word_selected.lower():
                st.success("Correct spelling!")
                # Prepare for the next word
                st.session_state.correct_spelling = True

                # Check if the list is now empty
                if not st.session_state.word_list:
                    st.balloons()
                    st.success("Congratulations! You have spelled all words correctly.")

                # Clear the cached data
                st.cache_data.clear()

                # Increment the input key
                st.session_state.input_key += 1
                st.rerun()
                
            # If the spelling is incorrect
            else:
                st.error("Incorrect spelling. Please try again.")
                # Set the correct spelling flag to False
                st.session_state.correct_spelling = False

# Run the app
if __name__ == "__main__":
    main()