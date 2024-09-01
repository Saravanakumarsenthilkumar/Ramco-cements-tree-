import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import csv
from collections import defaultdict
from langchain.llms import OpenAI
from datetime import datetime
import os

# Set up OpenAI API key
os.environ["OPEN_API_KEY"] = "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"
llm = OpenAI(openai_api_key=os.environ["OPEN_API_KEY"], temperature=0.6)

# Global variables
current_view = 0
locations_by_area = {}
total_co2_by_year = {}
df = None  # Define df as a global variable


# Function to open the chatbot window
def open_chatbot_window():
    chatbot_window = tk.Toplevel(window)
    chatbot_window.title("Chatbot")
    chatbot_window.geometry("600x400")

    chatbot_frame = ttk.Frame(chatbot_window)
    chatbot_frame.pack(padx=10, pady=10, fill=tk.BOTH)

    user_input_label = ttk.Label(chatbot_frame, text="Enter your text:")
    user_input_label.grid(row=0, column=0)

    user_input_entry = ttk.Entry(chatbot_frame, width=50)
    user_input_entry.grid(row=0, column=1)

    send_button = ttk.Button(chatbot_frame, text="Send", command=lambda: send_message(user_input_entry, chatbot_response_text))
    send_button.grid(row=0, column=2, padx=5)

    chatbot_response_text = tk.Text(chatbot_frame, wrap="word", height=15, width=70)
    chatbot_response_text.grid(row=1, column=0, columnspan=3, pady=5)

# Function to send message to chatbot and display response
def send_message(user_input_entry, chatbot_response_text):
    user_input = user_input_entry.get()
    if user_input:
        # Define a prompt to guide the chatbot to reply with information about the advantages of trees
        prompt = "Discuss the advantages of trees in sequestering carbon dioxide."
        
        # Generate response from chatbot
        response = llm.predict(prompt + " " + user_input)
        chatbot_response_text.insert(tk.END, f"User: {user_input}\n")
        chatbot_response_text.insert(tk.END, f"Chatbot: {response}\n\n")
        # Clear input field
        user_input_entry.delete(0, tk.END)


# Function to calculate age of the tree
def calculate_age(year_of_plantation):
    current_year = datetime.now().year
    return current_year - int(year_of_plantation)

# Function to calculate CO2 sequestered per year
def calculate_co2_sequestered(row):
    diameter = float(row['Diameter in M']) * 39.37  # Convert diameter from meters to inches
    height = float(row['Height in Ft'])
    year_of_plantation = int(row['Year of plantation'])
    
    age_of_tree = calculate_age(year_of_plantation)
    
    if diameter < 11:
        weight = 0.25 * diameter**2 * height
    else:
        weight = 0.15 * diameter**2 * height
    
    co2_sequestered_pounds = 1.5948 * weight / (age_of_tree)
    co2_sequestered_kg = co2_sequestered_pounds * 0.454
    return co2_sequestered_kg

# Function to read location data from CSV file
def read_location_data(file_path):
    locations_by_area = defaultdict(list)
    total_co2_by_year = defaultdict(float)
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            year_of_plantation = row['Year of plantation']
            location = row['Location']
            species = row['Name of species'].split(',')  # Splitting species by comma
            co2_sequestered = calculate_co2_sequestered(row)
            no_of_trees = int(row['No.s'])
            total_co2_calculated = no_of_trees * co2_sequestered
            locations_by_area[location].append((year_of_plantation, species, co2_sequestered, total_co2_calculated))
            total_co2_by_year[year_of_plantation] += total_co2_calculated
    return locations_by_area, total_co2_by_year

# Function to handle file upload and integrate both dataset uploading functionalities
def upload_dataset():
    global locations_by_area, total_co2_by_year, df
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        locations_by_area, total_co2_by_year = read_location_data(file_path)
        try:
            df = pd.read_csv(file_path)
            df['CO2 Sequestered per Year (kg)'] = df.apply(calculate_co2_sequestered, axis=1)
            df['Total_CO2_Calculated'] = df['No.s'] * df['CO2 Sequestered per Year (kg)'] # Calculate Total_CO2_Calculated
            update_view()
            messagebox.showinfo("Upload Successful", "Dataset uploaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset: {str(e)}")

# Function to display dataset in a table
def display_dataset(df, year_filter=None):
    global tree
    tree.delete(*tree.get_children())
    if year_filter is not None:
        filtered_df = df[df['Year of plantation'] == year_filter]
    else:
        filtered_df = df.copy()
    for index, row in filtered_df.iterrows():
        co2_per_year = "{:.2f}".format(row['CO2 Sequestered per Year (kg)']) # Format CO2 value to 2 decimal points
        total_co2_calculated = "{:.2f}".format(row['Total_CO2_Calculated']) # Format total CO2 value to 2 decimal points
        tree.insert('', 'end', values=(row['Year of plantation'], row['Name of species'], row['No.s'], row['Diameter in M'], row['Height in Ft'], co2_per_year, total_co2_calculated, '')) # Added an empty string for the additional column
    
    # Add a new row for total calculation and CO2 per yearwise
    if year_filter is not None:
        total_co2_calculated = filtered_df['Total_CO2_Calculated'].sum()
        total_co2_calculated = "{:.2f}".format(total_co2_calculated) # Format total CO2 value to 2 decimal points
        tree.insert('', 'end', values=('', '', '', '', '', '', f'Total: {total_co2_calculated}', f'Co2_per_yearwise: {total_co2_calculated}'))

# Function to update the view based on the current state
def update_view():
    global current_view, df
    if current_view == 0:
        display_dataset(df)
    elif current_view == 1:
        plot_data(df)
    elif current_view == 3:
        plot_year_vs_co2_per_yearwise(df)

# Function to plot CO2 sequestration data
def plot_data(df):
    plt.figure(figsize=(10, 6))
    species_names = df['Name of species']
    co2_sequestered = df['CO2 Sequestered per Year (kg)']
    plt.bar(species_names, co2_sequestered, color='skyblue')
    plt.xlabel('Species', fontsize=12)
    plt.ylabel('CO2 Sequestered per Year (kg)', fontsize=12)
    plt.title('CO2 Sequestration per Tree Species', fontsize=14)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

# Function to plot Year vs Co2_per_yearwise
def plot_year_vs_co2_per_yearwise(df):
    year_vs_co2_per_yearwise = df.groupby('Year of plantation')['Total_CO2_Calculated'].sum()
    years = year_vs_co2_per_yearwise.index
    co2_per_yearwise = year_vs_co2_per_yearwise.values

    plt.figure(figsize=(10, 6))
    plt.bar(years, co2_per_yearwise, color='blue')
    plt.xlabel('Year of Plantation', fontsize=12)
    plt.ylabel('Total CO2 Sequestered per Year (kg)', fontsize=12)
    plt.title('Year of Plantation vs Total CO2 Sequestered per Year (kg)', fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    for i, v in enumerate(co2_per_yearwise):
        plt.text(i, v + 0.1, str("{:.2f}".format(v)), ha='center', va='bottom')

    plt.show()

# Function to display top 10 species that absorb maximum carbon with visualization
def display_top_species_visualization():
    top_species = df.groupby('Name of species')['Total_CO2_Calculated'].sum().nlargest(10)
    
    # Extract species names and corresponding CO2 absorption values
    species_names = top_species.index
    co2_absorption = top_species.values
    
    # Create bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(species_names, co2_absorption, color='skyblue')
    plt.xlabel('Species', fontsize=12)
    plt.ylabel('Total CO2 Sequestered (kg)', fontsize=12)
    plt.title('Top 10 Species by CO2 Absorption', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
# Function to show top species by count of trees
def display_top_species_count():
    top_species_count = df.groupby('Name of species')['No.s'].sum().nlargest(10)
    
    # Extract species names and corresponding tree counts
    species_names = top_species_count.index
    tree_counts = top_species_count.values
    
    # Create bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(species_names, tree_counts, color='orange')
    plt.xlabel('Species', fontsize=12)
    plt.ylabel('Total Number of Trees', fontsize=12)
    plt.title('Top 10 Species by Tree Count', fontsize=14)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Function to switch to the Dataset view
def show_dataset():
    global current_view
    current_view = 0
    update_view()

# Function to switch to the CO2 sequestration per species view
def show_co2_sequestration():
    global current_view
    current_view = 1
    update_view()

# Function to switch to the Year vs Co2_per_yearwise view
def show_year_vs_co2_per_yearwise():
    global current_view
    current_view = 3
    update_view()

# Function to filter the table based on selected year
def filter_by_year():
    selected_year = int(year_filter_entry.get())
    display_dataset(df, year_filter=selected_year)

# Function to open a new window displaying characteristics of a selected location
def open_location_window():
    location_window = tk.Toplevel(window)
    location_window.title("Location Characteristics")
    location_window.geometry("400x300")
    create_main_window()

def show_species(root, locations_by_area, total_co2_by_year, area):
    locations = locations_by_area[area]
    output_window = tk.Toplevel(root)
    output_window.title(f"Species and CO2 Sequestered ({area})")
    
    # Display the information in a grid layout
    for i, (year, species, co2_sequestered, total_co2_calculated) in enumerate(locations):
        species_list = ", ".join(species)
        message = f"Year: {year}\nSpecies present: {species_list}\nCO2 Sequestered: {co2_sequestered:.2f} kg\nTotal CO2 Calculated: {total_co2_calculated:.2f} kg"
        
        # Calculate row and column index for the current label
        row_index = i // 5
        col_index = i % 5
        
        # Create label and place it in the grid
        label = tk.Label(output_window, text=message)
        label.grid(row=row_index, column=col_index, padx=5, pady=5)
    
    # Display total CO2 sequestered
    total_co2_year = total_co2_by_year.get(year)
    message = f"Total CO2 Sequestered in {year}: {total_co2_year:.2f} kg"
    row_index = len(locations) // 5 + 1
    label_total = tk.Label(output_window, text=message)
    label_total.grid(row=row_index, column=0, columnspan=5, padx=5, pady=5)


# Function to create the main window
def create_main_window():
    root = tk.Tk()
    root.title("Location Buttons")

    # Light blue color
    light_blue = "#ADD8E6"

    # Width and height of the buttons
    button_width = 60
    button_height = 1

    # Create buttons for each area with light blue background and same size
    for area in locations_by_area.keys():
        button = tk.Button(root, text=area, bg=light_blue, width=button_width, height=button_height, command=lambda area=area: show_species(root, locations_by_area, total_co2_by_year, area))
        button.pack(pady=5)

    # Run the Tkinter event loop
    root.mainloop()

# Create tkinter window
window = tk.Tk()
window.title("CO2 Sequestration Calculator")
window.geometry("800x650")

# Create upload button
upload_button = ttk.Button(window, text="Upload Dataset", command=upload_dataset)
upload_button.pack(pady=10)

# Create a frame for year filter
filter_frame = ttk.Frame(window)
filter_frame.pack(padx=10, pady=5, fill=tk.BOTH)

year_filter_label = ttk.Label(filter_frame, text="Filter by Year of plantation:")
year_filter_label.grid(row=0, column=0)

year_filter_entry = ttk.Entry(filter_frame, width=10)
year_filter_entry.grid(row=0, column=1)

filter_button = ttk.Button(filter_frame, text="Filter", command=filter_by_year)
filter_button.grid(row=0, column=2, padx=5)

# Create a frame to hold the text widget
tree_frame = ttk.Frame(window)
tree_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

tree_columns = ['Year of plantation', 'Name of species', 'No.s', 'Diameter in M', 'Height in Ft', 'CO2 Sequestered per Year (kg)', 'Total_CO2_Calculated', 'Co2_per_yearwise']

tree = ttk.Treeview(tree_frame, columns=tree_columns, show='headings')
for col in tree_columns:
    tree.heading(col, text=col)
tree.pack(fill=tk.BOTH, expand=True)

# Create navigation buttons
dataset_button = ttk.Button(window, text="Show Dataset", command=show_dataset)
dataset_button.pack(side=tk.LEFT, padx=10)
co2_sequestration_button = ttk.Button(window, text="Show CO2 Sequestration", command=show_co2_sequestration)
co2_sequestration_button.pack(side=tk.LEFT, padx=10)
top_species_button = ttk.Button(window, text="Show Top 10 Species", command=display_top_species_visualization)
top_species_button.pack(side=tk.LEFT, padx=10)
top_species_count_button = ttk.Button(window, text="Show Top Species Count", command=display_top_species_count)
top_species_count_button.pack(side=tk.LEFT, padx=10)
year_vs_co2_per_yearwise_button = ttk.Button(window, text="Show Year vs Co2_per_yearwise", command=show_year_vs_co2_per_yearwise)
year_vs_co2_per_yearwise_button.pack(side=tk.LEFT, padx=10)

# Create location button
location_button = ttk.Button(window, text="View Location Characteristics", command=open_location_window)
location_button.pack(side=tk.RIGHT, padx=10, pady=5)


# Create chatbot button
chatbot_button = ttk.Button(window, text="Open Chatbot", command=open_chatbot_window)
chatbot_button.pack(side=tk.RIGHT, padx=10)

# Run the tkinter event loop
window.mainloop()