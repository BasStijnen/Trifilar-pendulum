
# use the marker tracker git repository to track multiple 'known markers in a video'

import numpy as np
import cv2
from moviepy.editor import VideoFileClip
import MarkerTracker
import math
import csv
import os

# get the video and get rid of the audio


def no_audio(path_input, path_output):
    videoclip = VideoFileClip(path_input)
    new_clip = videoclip.without_audio()
    #change directory to out_put directory
    os.chdir(path_output)
    new_clip.write_videofile('No_audio.mp4')
    #create a VideoCapture object and read from inputfile
    cap = cv2.VideoCapture('No_audio.mp4')
    return cap



# setup output file
def output_file_generation():
    centre_dot = open('centre_dot.csv', 'w')
    Point_1 = open('Point_1.csv', 'w')
# Add headers to the output
    writer = csv.writer(centre_dot, delimiter = ',', dialect = 'excel', lineterminator = '\n')
    writer.writerow(['frame','X','Y'])
    writer = csv.writer(Point_1, delimiter = ',', dialect = 'excel', lineterminator = '\n')
    writer.writerow(['frame','X','Y'])
    centre_dot.close
    Point_1.close




def track_all(cap, order1, order2, size_of_kernel):
 # Main loop
    tracker1 = MarkerTracker.MarkerTracker(order1, size_of_kernel, 5.0)
    tracker2 = MarkerTracker.MarkerTracker(order2, size_of_kernel, 5.0)
    counter = 0
    while cap.isOpened():
        counter += 1
        # Read a new image from the file.
        ret, frame = cap.read()

        
        # Halt if reading failed.
        if not ret:
            print('end of frame')
            break


        # Convert image to grayscale.
        gray_scale_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Locate marker in image.
        marker_pose_1 = tracker1.locate_marker(gray_scale_image)
        store_marker_location(counter, marker_pose_1, 'Point_1.csv')

        marker_pose_2 = tracker2.locate_marker(gray_scale_image)
        store_marker_location(counter, marker_pose_2, 'centre_dot.csv')
       
                
        # Mark the center of the marker
        annotate_frame_with_detected_marker(frame, marker_pose_1, order1, size_of_kernel)
        annotate_frame_with_detected_marker(frame, marker_pose_2, order2, size_of_kernel)

        # Show the annotated image.
        #norm_image = cv2.normalize(tracker.frame_sum_squared, None, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)
        #cv2.imshow('marker_response', norm_image)
        cv2.imshow('frame', frame)


        # Break the look if the key 'q' was pressed.
        key_value = cv2.waitKey(1)
        if key_value & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
    return frame

def store_marker_location(counter, marker_pose, output_file):
   # string_to_file = "%3d %f %f" % (counter, marker_pose.x, marker_pose.y)
   # print(string_to_file[0:-1])
    with open(output_file, 'a', newline='') as location:
        writer = csv.writer(location)
        writer.writerow([counter, marker_pose.x, marker_pose.y])
        location.close

def annotate_frame_with_detected_marker(frame, marker_pose, order_of_marker_input, size_of_kernel_input):
    line_width_of_circle = 1
    if marker_pose.quality > 0.8:
        marker_color = (0, 255, 0)
    else:
        marker_color = (255, 0, 255)
    cv2.circle(frame, (int(marker_pose.x), int(marker_pose.y)), int(size_of_kernel_input / 2), marker_color, line_width_of_circle)
    dist = 50
    direction_line_width = 1
    point1 = (int(marker_pose.x), int(marker_pose.y))
    theta = marker_pose.theta
    for k in range(order_of_marker_input):
        theta += 2 * math.pi / order_of_marker_input
        point2 = (math.trunc(marker_pose.x + dist * math.cos(theta)),math.trunc(marker_pose.y + dist * math.sin(theta)))
        cv2.line(frame, point1, point2, marker_color, direction_line_width)




