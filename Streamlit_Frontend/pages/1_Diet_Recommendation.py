import streamlit as st
import pandas as pd
from Generate_Recommendations import Generator
from random import uniform as rnd
from ImageFinder.ImageFinder import get_images_links as find_image
from streamlit_echarts import st_echarts

st.set_page_config(page_title="Automatic Diet Recommendation", page_icon="💪", layout="wide")

disease_options = ["Diabetes", "Hypertension", "Obesity", "Heart Disease", "Anemia", "Osteoporosis"]
nutrition_values = ['Calories', 'FatContent', 'SaturatedFatContent', 'CholesterolContent', 'SodiumContent', 'CarbohydrateContent', 'FiberContent', 'SugarContent', 'ProteinContent']

if 'generated' not in st.session_state:
    st.session_state.generated = False
    st.session_state.recommendations = None

class Person:
    def __init__(self, age, height, weight, gender, activity, meals_calories_perc, weight_loss, diseases):
        self.age = age
        self.height = height
        self.weight = weight
        self.gender = gender
        self.activity = activity
        self.meals_calories_perc = meals_calories_perc
        self.weight_loss = weight_loss
        self.diseases = diseases

    def calories_calculator(self):
        if self.gender == 'Male':
            return 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            return 10 * self.weight + 6.25 * self.height - 5 * self.age - 161

    def generate_recommendations(self):
        total_calories = self.weight_loss * self.calories_calculator()
        recommendations = []
        
        for meal, percentage in self.meals_calories_perc.items():
            meal_calories = percentage * total_calories
            generator = Generator([meal_calories] + [rnd(10, 30) for _ in range(8)], self.diseases)
            
            try:
                response = generator.generate()
                if response and response.json().get('output'):
                    recommended_recipes = response.json()['output']
                    for recipe in recommended_recipes:
                        recipe['image_link'] = find_image(recipe['Name'])
                    recommendations.extend(recommended_recipes)
                else:
                    st.warning(f"No recommendations found for {meal}.")
            except Exception as e:
                st.error(f"Error generating recommendations for {meal}: {e}")
                continue
        
        return recommendations if recommendations else None

st.markdown("<h1 style='text-align: center;'>Automatic Diet Recommendation</h1>", unsafe_allow_html=True)

with st.form("recommendation_form"):
    st.write("Modify the values and click the Generate button to use")
    age = st.number_input('Age', min_value=2, max_value=120, step=1)
    height = st.number_input('Height(cm)', min_value=50, max_value=300, step=1)
    weight = st.number_input('Weight(kg)', min_value=10, max_value=300, step=1)
    gender = st.radio('Gender', ('Male', 'Female'))
    activity = st.select_slider('Activity', options=['Little/no exercise', 'Light exercise', 'Moderate exercise (3-5 days/wk)', 'Very active (6-7 days/wk)', 'Extra active (very active & physical job)'])
    weight_loss_option = st.selectbox('Choose your weight loss plan:', ["Maintain weight", "Mild weight loss", "Weight loss", "Extreme weight loss"])
    weight_loss = [1, 0.9, 0.8, 0.6][["Maintain weight", "Mild weight loss", "Weight loss", "Extreme weight loss"].index(weight_loss_option)]
    
    number_of_meals = st.slider('Meals per day', min_value=3, max_value=5, step=1, value=3)
    if number_of_meals == 3:
        meals_calories_perc = {'breakfast': 0.35, 'lunch': 0.40, 'dinner': 0.25}
    elif number_of_meals == 4:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'dinner': 0.25}
    else:
        meals_calories_perc = {'breakfast': 0.30, 'morning snack': 0.05, 'lunch': 0.40, 'afternoon snack': 0.05, 'dinner': 0.20}

    diseases = st.multiselect("Select any existing health conditions:", disease_options)
    generated = st.form_submit_button("Generate")

if generated:
    st.session_state.generated = True
    person = Person(age, height, weight, gender, activity, meals_calories_perc, weight_loss, diseases)
    recommendations = person.generate_recommendations()
    st.session_state.recommendations = recommendations

if st.session_state.generated:
    st.header("Diet Recommendations")
    if st.session_state.recommendations:
        st.write("Recommendations generated based on your inputs.")
        for recipe in st.session_state.recommendations:
            expander = st.expander(recipe['Name'])
            expander.markdown(f'<div><center><img src={recipe["image_link"]} alt="{recipe["Name"]}"></center></div>', unsafe_allow_html=True)
            nutritions_df = pd.DataFrame({value: [recipe[value]] for value in nutrition_values})
            expander.dataframe(nutritions_df)
            expander.markdown("### Ingredients:")
            for ingredient in recipe['RecipeIngredientParts']:
                expander.markdown(f"- {ingredient}")
            expander.markdown("### Recipe Instructions:")
            for instruction in recipe['RecipeInstructions']:
                expander.markdown(f"- {instruction}")
            expander.markdown("### Cooking and Preparation Time:")
            expander.markdown(f"- Cook Time: {recipe['CookTime']} min\n- Prep Time: {recipe['PrepTime']} min\n- Total Time: {recipe['TotalTime']} min")
        
        selected_recipe = st.selectbox("Select a recipe for nutritional overview:", [recipe['Name'] for recipe in st.session_state.recommendations])
        selected_data = next(recipe for recipe in st.session_state.recommendations if recipe['Name'] == selected_recipe)
        options = {
            "title": {"text": "Nutrition Values", "subtext": selected_recipe, "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"orient": "vertical", "left": "left"},
            "series": [{
                "name": "Nutrition values",
                "type": "pie",
                "radius": "50%",
                "data": [{"value": selected_data[nutrient], "name": nutrient} for nutrient in nutrition_values],
            }],
        }
        st_echarts(options=options, height="600px")
    else:
        st.warning("No recommendations available.")
