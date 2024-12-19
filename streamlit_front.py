from typing import Set
import os
import streamlit as st
import entitylinker as response
from loguru import logger
from streamlit_chat import message
import time

import requests

# from backend.core import run_llm

#
# def send_data():
#     ####  to DO
#     st.toast('sending conversation to database......')
#     url: str = os.getenv("SUPABASE_URL")
#     logger.info(f'url: {url}')
#     key: str = os.getenv("SUPABASE_KEY")
#     supabase: Client = create_client(url, key)
#
#     meta = "conversation"
#
#     json_value = {'meta': meta, 'conversation': st.session_state['chat_history']}
#
#     try:
#      data = supabase.table('data_meta').insert(json_value).execute()
#     except Exception as e:
#         logger.error(e)
#         st.toast('failed to send data to database')
#         return
#
#     st.toast("success :sunglasses:")
#     reset()
#
#
# def reset():
#     if "chat_answers_history" in st.session_state:
#         st.session_state["chat_answers_history"] = []
#     if "user_prompt_history" not in st.session_state:
#         st.session_state["user_prompt_history"] = []
#     if  "chat_history" not in st.session_state:
#         st.session_state["chat_history"] = []
#
# def history_valid(history):
#     try:
#         length = len(history)
#         history_str = history[length - 1]
#     except IndexError:
#         history_str = 'No histrory'
#
#     return history_str
# def generate_response():
#
#     for generated_response, user_query in zip(
#             st.session_state["chat_answers_history"],
#             st.session_state["user_prompt_history"],
#     ):
#         message(
#             user_query,
#             is_user=True,
#         )
#         message(generated_response)
# def update_hist(txt):
#     try:
#         index = len(st.session_state['chat_history']) - 1
#         st.session_state['chat_history'][index]['system'] = txt
#         st.session_state['chat_answers_history'][index] = txt
#         st.write('history available')
#     except IndexError:
#         st.write('###no history available')
#
#
# def hist_clicked(txt):
#     update_hist(txt)
#     st.write("Changes to conversation have been updated")
#
#     message(
#         txt,
#         avatar_style= "pixel-art-neutral"
#     )
#
#
#
# def display_hist(history):
#
#     try:
#         length = len(history)
#         history_str = history[length - 1]
#     except IndexError:
#         history_str = 'No histrory'
#         history_str = 'No history available'
#
#
#     return st.text_area(
#         "Text to analyze",
#         history_str,
#         key = 'history_ed',
#     )
#
#
#
# def chat_api_call(payload: dict):
#
#     headers = {'Content-Type': 'application/json'}
#
#
#     logger.info(f"Payload being sent:{payload}")
#
#     logger.info(f"question: {type(payload['question'])}")
#     logger.info(f"chat: {type(payload['chat_history'])}")
#
#     try:
#         logger.info(f"chat_histrory: {payload['chat_history'][0]}")
#         logger.info(f"chat_histrory: {type(payload['chat_history'][0])}")
#     except IndexError:
#         logger.info(f"chat_histrory: {payload['chat_history']}")
#
#
#     logger.info(f"context: {type(payload['context'])}")
#
#
#     # POST request
#     response = requests.post(url, json=payload, headers=headers)
#
#     # Print response for debugging
#     logger.info(f"Response status code: {response.status_code}")
#     logger.info(f"Response body: {response.text}")
#
#     if response.status_code == 200:
#         logger.info("Question sent successfully")
#         return response.json()
#     else:
#         # print(f"Failed to send question, status code: {response.status_code}")
#         return response.json()
#
#
# def create_sources_string(source_urls: Set[str]) -> str:
#     if not source_urls:
#         return ""
#     sources_list = list(source_urls)
#     sources_list.sort()
#     sources_string = "sources:\n"
#     for i, source in enumerate(sources_list):
#         sources_string += f"{i+1}. {source}\n"
#     return sources_string
#
def display_convo(user, bot):



    if user is None:
        return

    with st.chat_message("assistant"):


        for generated_response, user_query in zip(
                bot,
                user,
        ):
            message(
                user_query,
                is_user=True,
                # key='assistant'
            )
            message(generated_response)

#
@st.cache_data(experimental_allow_widgets=True)
def laisa(prompt):
    # Display user message in chat message container
    # st.chat_message("user").markdown(prompt)
    # Add user message to chat history

    payload = {
        "question": prompt,
        "chat_history": st.session_state['chat_history'],  # This is already a list, so no need for conditional logic
        "context": ""
    }

    logger.info(f"payload: {payload}")

    generated_response = response

    logger.info(f"Generated response: {generated_response}")
    # logger.info(f"Generated type: {type(generated_response['source_documents'])}")
    # logger.info(f"Generated length: {len(generated_response['source_documents'])}")

    # try:
    #     sources = set(
    #         [doc['metadata']["source"] for doc in generated_response["source_documents"]]
    #     )
    # except KeyError as e:
    #     sources = set()

    formatted_response = (
        f"{generated_response['llm_output']} \n\n {generated_response['entities']}"
    )

    # response = f"Echo: {formatted_response}"

    logger.info(f"chat_history: {st.session_state.chat_history}")
    logger.info(f'chat_history type:{type(st.session_state.chat_history)}')

    try:
        logger.info(f"chat_history value at 0: {st.session_state.chat_history[0]}")
        logger.info(f"chat_history value type: {type(st.session_state.chat_history[0])}")
    except IndexError as e:
        logger.info(f"no value in chat_history")

    st.session_state.chat_history.append({'human': prompt, 'system': generated_response["answer"]})
    st.session_state.user_prompt_history.append(prompt)
    st.session_state.chat_answers_history.append(formatted_response)

    logger.info(f"chat_history: {st.session_state.chat_history}")
    logger.info(f'chat_history type:{type(st.session_state.chat_history)}')

    # Display assistant response in chat message container


st.header("LAISA🦜🔗 ")

# Initialize chat history
if (
    "chat_answers_history" not in st.session_state
    and "user_prompt_history" not in st.session_state
    and "chat_history" not in st.session_state
):
    st.session_state["chat_answers_history"] = []
    st.session_state["user_prompt_history"] = []
    st.session_state["chat_history"] = []
    st.session_state.key= 'main_session'

update = False



if prompt := st.chat_input("Talk to me"):
    laisa(prompt)
    update = True

    # st.session_state.messages.append({"role": "assistant", "content": response})




# col1, col2, col3 = st.columns(3)
#
# with col1:
#     if st.button("Save sample:thumbsup:"):
#         send_data()
#
#
#
# with col3:
#     if st.button('reset ::repeat::'):
#         reset()
#
#
# with st.sidebar:
#     st.session_state.user = "sidebar"
#     txt = display_hist(st.session_state["chat_answers_history"])
#
#     st.button(':white_check_mark:', on_click=hist_clicked(txt), key='change_hist')



display_convo(st.session_state['user_prompt_history'], st.session_state['chat_answers_history'])



# <script defer src="https://analytics.eu.umami.is/script.js" data-website-id="be9ae228-3515-40ae-ae82-d5c122bc6811"></script>