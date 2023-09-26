#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 2023

@author: basstijnen
"""
from datetime import datetime
import os
from functions_MoI_rig2 import Find_Moment_Of_Inertia, print_tau
from track_marker_moi import track_all, no_audio, output_file_generation
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time



canvas = None
#function to redirect standard output to the text widget for error control
def update_text_output():
    text_output.config(state=tk.NORMAL)
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, output_buffer)
    text_output.see(tk.END)  # Auto-scroll to the end of the text
    text_output.config(state=tk.DISABLED)
#fucntion for info window
def show_info_popup():
    info_window = tk.Toplevel()
    info_window.title("Software info and licence")
    # Load and display an image
    logo_image = tk.PhotoImage(file="UCD_logo.png")  # Replace with your image file
    logo_label = tk.Label(info_window, image=logo_image)
    logo_label.image = logo_image  # Keep a reference to the image
    logo_label.grid(row=0, column=1, padx=10, pady=10, rowspan=3)

    # Create a label with the information message
    info_text = "This software was built to calculate the Mass Moment of Inertia of an object.\n"
    info_text += "It is complementary to the Trifilar Pendulum project DOI: 10.17632/zww548rfbn.3\n"
    info_text += "This project is licensed under a CCBY4.0\n\n"
    info_text += "This project was developed at UCD School of Engineering"
    
    info_label = tk.Label(info_window, text=info_text)
    info_label.grid(row=0, column=0, padx=10, pady=10)




# main function that calculates MoI from a .mp4 video
def process_data():
    global output_buffer
    global canvas
    # Clear the Text widget before processing data
    text_output.config(state=tk.NORMAL)
    text_output.delete(1.0, tk.END)
    text_output.config(state=tk.DISABLED)

    #get the selected input path
    input_path = input_path_var.get()
    #get the selected output path
    output_path = output_path_var.get()
    #set mass (m) in g
    m_input = (mass_entry.get())
    #set frame rate (fps)
    fps_input = (fps_entry.get())
    #set pendulum radius R in (mm)
    R_input = (R_entry.get())
    #set cable length in mm
    L_input = (L_entry.get())
    # set centre dot marker size
    order1 = int(centre_dot_entry.get())
    # set outer dot maker size
    order2 = int(outer_dot_entry.get())
    #set kernel size of both markers
    size_of_kernel = int(kernal_size_entry.get())
    #get time and day in order to label output folders
    today = datetime.now()
    ## check if any of the input fields are empty
    if not all([m_input, fps_input, R_input, L_input]):
        output_buffer += "Warning: Please fill in all input fields!\n"
        update_text_output()
        return  # Return without processing data if any input field is empty

    # Convert input values to floats
    try:
        m = float(m_input)
        fps = float(fps_input)
        R = float(R_input)
        L = float(L_input)
    except ValueError:
        output_buffer += "Warning: Invalid input! Please enter numeric values.\n"
        update_text_output()
        return  # Return without processing data if any input is invalid

    output_buffer += "Process: Generating output folder \n"
    update_text_output()
    window.update()
    output_path = output_path + today.strftime('%Y%m%d%H%M')
    os.mkdir(output_path)
    # safe video without audio
    output_buffer += "Process: Removing Audio from video file \n"
    update_text_output()
    window.update()
    cap = no_audio(input_path, output_path)
    # create output csv files
    output_file_generation()
    # perform tracking and safe to CSV files
    output_buffer += "Process: Tracking markers and saving to CSV files \n"
    update_text_output()
    window.update()
    track_all(cap, order1, order2, size_of_kernel)
    # calculate the MoI
    time.sleep(2)
    output_buffer +="Process: Calculation of MoI \n"
    window.update()
    update_text_output()
    I, frame, angle = Find_Moment_Of_Inertia(output_path, fps, m, R, L)
    Tau = print_tau(output_path, fps)
    
    I_label_var.set(f"I:{I}")
    Tau_label_var.set(f"Tau: {Tau}")
    angle_label_var.set(f"angle:{angle}")
    
    #plot the coresponding oscillation
    fig = plt.figure(figsize=(6,4), dpi=80)
    ax = fig.subplots()
    ax.plot(frame['frame_num'], frame['polar_12'])
    ax.set_xlabel('time [s]')
    ax.set_ylabel('rotation [Rad]')
 
    #clear previous plot and redraw the canvas
    if canvas:
        canvas.get_tk_widget().pack_forget()
    canvas = FigureCanvasTkAgg(fig, master=output_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()
    output_buffer +="Done! \n"
    update_text_output()
    window.update()

def browse_input_path():
    path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4")])
    input_path_var.set(path)

def browse_output_path():
    path = filedialog.askdirectory()
    output_path_var.set(path)    

#create the main window
window = tk.Tk()

#set the window title
window.title("MoI Rig SW interface")

#create a text widget for terminal output
text_output = tk.Text(window, height=3, width=50)
text_output.pack(side=tk.BOTTOM, padx=10, pady=10)

# creat frame for input section
input_frame = tk.Frame(window)
input_frame.pack(side=tk.LEFT, padx=10, pady=10)

output_frame = tk.Frame(window)
output_frame.pack(side=tk.RIGHT, padx=10, pady=10)

#create a label and entry for input path
input_path_label = tk.Label(input_frame, text = "input video:")
input_path_label.pack()

input_path_var = tk.StringVar()
input_path_entry = tk.Entry(input_frame, textvariable=input_path_var)
input_path_entry.pack()

#create a button to browse input path
input_path_button = tk.Button(input_frame, text="Browse", command=browse_input_path)
input_path_button.pack()

#create a label and entry for output path
output_path_label = tk.Label(input_frame, text = "output path:")
output_path_label.pack()

output_path_var = tk.StringVar()
output_path_entry = tk.Entry(input_frame, textvariable=output_path_var)
output_path_entry.pack()

#create a button to browse input path
output_path_button = tk.Button(input_frame, text="Browse", command=browse_output_path)
output_path_button.pack()


# Create a label and entry for mass (m)
mass_label = tk.Label(input_frame, text="Combined mass of table and object (g):")
mass_label.pack()

mass_entry = tk.Entry(input_frame)
mass_entry.pack()

# Create a label and entry for frame rate (fps)
fps_label = tk.Label(input_frame, text="Frame Rate (fps):")
fps_label.pack()

default_fps = "50"
fps_entry = tk.Entry(input_frame)
fps_entry.insert(tk.END, default_fps)
fps_entry.pack()

# Create a label and entry for the plate radius
R_label = tk.Label(input_frame, text="Radius (mm):")
R_label.pack()

default_R = "225"
R_entry = tk.Entry(input_frame)
R_entry.insert(tk.END, default_R)
R_entry.pack()

# Create a label and entry for cable length (mm)
L_label = tk.Label(input_frame, text="Length of the cables in (mm):")
L_label.pack()

default_L = "1250"
L_entry = tk.Entry(input_frame)
L_entry.insert(tk.END, default_L)
L_entry.pack()

# Create a label and entry for centre dot size
centre_dot_label = tk.Label(input_frame, text="Centre dot size:")
centre_dot_label.pack()

centre_order = "5"
centre_dot_entry = tk.Entry(input_frame)
centre_dot_entry.insert(tk.END, centre_order)
centre_dot_entry.pack()

# Create a label and entry for outer dot size
outer_dot_label = tk.Label(input_frame, text="Outer dot size:")
outer_dot_label.pack()

outer_order = "4"
outer_dot_entry = tk.Entry(input_frame)
outer_dot_entry.insert(tk.END, outer_order)
outer_dot_entry.pack()

# Create a label and entry for kernal size
kernal_size_label = tk.Label(input_frame, text="Kernal size:")
kernal_size_label.pack()

kernal_size = "80"
kernal_size_entry = tk.Entry(input_frame)
kernal_size_entry.insert(tk.END, kernal_size)
kernal_size_entry.pack()


#display output numbers MoI 
I_label_var = tk.StringVar()
I_label = tk.Label(output_frame, text="Mass Moment of Inertiain in mm^2 kg:", anchor=tk.W)
I_label.pack(fill=tk.X)

I_value_label = tk.Label(output_frame, textvariable=I_label_var, anchor = tk.W)
I_value_label.pack(fill=tk.X)

#display output number Tau
Tau_label_var = tk.StringVar()
Tau_label = tk.Label(output_frame, text = "Period of Oscillation in sec:",anchor = tk.W)
Tau_label.pack(fill=tk.X)

Tau_value_label = tk.Label(output_frame, textvariable= Tau_label_var, anchor=tk.W)
Tau_value_label.pack(fill=tk.X)

#display output number excitation angle
angle_label_var = tk.StringVar()
angle_label = tk.Label(output_frame, text = "Excitation angle in deg:",anchor = tk.W)
angle_label.pack(fill=tk.X)

angle_value_label = tk.Label(output_frame, textvariable= angle_label_var, anchor=tk.W)
angle_value_label.pack(fill=tk.X)



#create a canvas to display the plot
fig = plt.figure(figsize=(6,4), dpi=80)
canvas = FigureCanvasTkAgg(fig, master=output_frame)
canvas.draw()
canvas.get_tk_widget().pack()

#create a button to process the data
Process_button = tk.Button(input_frame, text="Process", command=process_data)
Process_button.pack()

info_button = tk.Button(output_frame, text="Info", command=show_info_popup)
info_button.pack(padx=20, pady=20)

#start main event loop
output_buffer = ""
window.mainloop()





