# app.py
import streamlit as st
import os
from utils.template_utils import (
    load_all_templates, 
    get_template_by_id,
    fill_template,
    extract_template_variables,
    filter_templates_by_dimensions
)
from utils.llm_utils import (
    initialize_llm,
    recommend_templates,
    adjust_template_to_use_case,
    refine_output,
    fully_adapt_template  # Import the new function
)
from utils.dimension_definitions import (
    get_scale_options,
    get_engagement_options,
    get_scale_definition,
    get_engagement_definition
)

# Set page config
st.set_page_config(
    page_title="Participatory Design Templates",
    page_icon="🔄",
    layout="wide"
)

# Initialize session state variables if they don't exist
if "step" not in st.session_state:
    st.session_state.step = 1
if "selected_template" not in st.session_state:
    st.session_state.selected_template = None
if "filled_template" not in st.session_state:
    st.session_state.filled_template = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "llm" not in st.session_state:
    st.session_state.llm = None
if "user_description" not in st.session_state:
    st.session_state.user_description = ""
if "selected_scale" not in st.session_state:
    st.session_state.selected_scale = None
if "selected_engagement" not in st.session_state:
    st.session_state.selected_engagement = None

# Initialize the app if it hasn't been initialized yet
if "templates" not in st.session_state:
    with st.spinner("Initializing application..."):
        # Load all templates
        templates = load_all_templates()
        st.session_state.templates = templates
        
        # Initialize the LLM (this is optional - will use keyword-based fallback if not available)
        llm = initialize_llm()
        st.session_state.llm = llm
        
        if llm:
            st.success("✅ LLM loaded successfully!")
        else:
            st.info("ℹ️ Running in fallback mode without LLM capabilities")

# App title
st.title("Participatory Design Template Generator")

# App description
st.markdown("""
This tool helps you generate customized participatory design templates for your specific use case.
1. Describe your use case and requirements
2. Select scale and engagement level
3. Choose from recommended templates
4. Refine the template through conversation
""")

# Step 1: Get use case description
if st.session_state.step == 1:
    st.header("1. Describe Your Use Case")
    
    # Use case input with session state to preserve input when moving between steps
    st.text_area(
        "Describe your participatory design scenario:",
        key="use_case_input",
        value=st.session_state.user_description,
        height=150,
        help="What are you trying to achieve with participatory design?"
    )
    
    if st.button("Next: Select Dimensions"):
        st.session_state.user_description = st.session_state.use_case_input
        st.session_state.step = 2
        st.rerun()
        # st.rerun() is deprecated in favor of st.rerun()

# Step 2: Select scale and engagement levels
elif st.session_state.step == 2:
    st.header("2. Select Scale and Engagement Level")
    
    # Scale selection
    st.subheader("Scale")
    for scale in get_scale_options():
        st.markdown(f"**{scale.capitalize()}**: {get_scale_definition(scale)}")
    
    st.selectbox(
        "Select the scale of your participatory design activity:",
        options=get_scale_options(),
        format_func=lambda x: x.capitalize(),
        key="scale_input",
        index=0 if st.session_state.selected_scale is None else get_scale_options().index(st.session_state.selected_scale)
    )
    
    # Engagement selection
    st.subheader("Engagement Level")
    for engagement in get_engagement_options():
        st.markdown(f"**{engagement.capitalize()}**: {get_engagement_definition(engagement)}")
    
    st.selectbox(
        "Select the engagement level of your participatory design activity:",
        options=get_engagement_options(),
        format_func=lambda x: x.capitalize(),
        key="engagement_input",
        index=0 if st.session_state.selected_engagement is None else get_engagement_options().index(st.session_state.selected_engagement)
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Back"):
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("Next: View Templates"):
            st.session_state.selected_scale = st.session_state.scale_input
            st.session_state.selected_engagement = st.session_state.engagement_input
            st.session_state.step = 3
            st.rerun()

# Step 3: Show recommended templates based on scale and engagement
elif st.session_state.step == 3:
    st.header("3. Select a Template")
    
    # Filter templates based on selected dimensions
    filtered_templates = filter_templates_by_dimensions(
        st.session_state.templates,
        st.session_state.selected_scale,
        st.session_state.selected_engagement
    )
    
    if filtered_templates:
        st.success(f"Found {len(filtered_templates)} templates matching your criteria")
        
        # Display templates in a card-like format
        for i, template in enumerate(filtered_templates):
            with st.container():
                st.markdown(f"### {template['name']}")
                st.markdown(f"*{template['description']}*")
                
                if st.button(f"Select this Template", key=f"select_{i}"):
                    selected_template = get_template_by_id(template["id"])
                    st.session_state.selected_template = selected_template
                    
                    # Use the new function to fully adapt the template to the user's use case
                    with st.spinner("Adapting template to your use case..."):
                        adapted_template = fully_adapt_template(
                            selected_template,
                            st.session_state.user_description,
                            st.session_state.llm
                        )
                        
                        # Set the adapted template as the filled template
                        st.session_state.filled_template = adapted_template
                    
                    st.session_state.step = 4
                    st.rerun()
                
                st.markdown("---")
    else:
        st.warning("No templates found matching your selected criteria")
        st.markdown("Try selecting different scale or engagement levels, or create a new template.")
    
    if st.button("Back to Dimension Selection"):
        st.session_state.step = 2
        st.rerun()

# Step 4: Refinement through conversation (Combined customization and chat)
elif st.session_state.step == 4:
    st.header(f"4. Refine Template: {st.session_state.selected_template['name']}")
    
    # Create two columns for chat and preview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Conversation")
        
        # Add initial message if chat history is empty
        if not st.session_state.chat_history:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I've adapted the template to your use case. You can review it on the right and ask me to make any specific changes or improvements."
            })
        
        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**You**: {message['content']}")
            else:
                st.markdown(f"**Assistant**: {message['content']}")
        
        # Input for refinement
        user_feedback = st.text_area("How would you like to refine the template?", "", height=100)
        
        if st.button("Send Request"):
            if user_feedback:
                # Add user message to chat history
                st.session_state.chat_history.append({"role": "user", "content": user_feedback})
                
                # Process the feedback using the LLM
                with st.spinner("Refining template..."):
                    refined_output = refine_output(
                        st.session_state.filled_template,
                        user_feedback,
                        st.session_state.llm
                    )
                    
                    # Update the filled template
                    st.session_state.filled_template = refined_output
                    
                    # Add assistant message to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": "I've updated the template based on your request."
                    })
                
                # Force a rerun to update the UI
                st.rerun()
    
    with col2:
        st.subheader("Template Preview")
        st.markdown(st.session_state.filled_template)
        
        # Download option
        st.download_button(
            label="Download Template as Markdown",
            data=st.session_state.filled_template,
            file_name="participatory_design_template.md",
            mime="text/markdown"
        )
    
    # Back button
    if st.button("Back to Templates"):
        st.session_state.step = 3
        st.rerun()

# Reset button (available on all steps)
if st.button("Start Over"):
    # Reset all relevant session state variables
    st.session_state.step = 1
    st.session_state.selected_template = None
    st.session_state.filled_template = ""
    st.session_state.chat_history = []
    st.session_state.user_description = ""
    st.session_state.selected_scale = None
    st.session_state.selected_engagement = None
    
    # Force a rerun to update the UI
    st.rerun()

# Footer
st.markdown("---")
st.markdown("Participatory Design Template Generator - Powered by HuggingFace & Streamlit")