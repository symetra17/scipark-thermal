import cv2
import numpy as np

def croppping(img,target_height,target_width,offset):
    originalwidth = img.shape[1]
    originalheight = img.shape[0]
    img_copy = img.copy()
    startx = (originalwidth - target_width)//2 + offset['x']
    endx=startx+target_width 
    starty = (originalheight - target_height)//2 + offset['y']
    endy=starty+target_height  
    if (len(img.shape))<3:
        img = img_copy[starty:endy, startx:endx]
    else:
        img = img_copy[starty:endy, startx:endx, 0:3]
    return img

def draw_rectangle(img,box,color,thick):
    left=int(box[0])
    top=int(box[1])
    right=int(box[0]+box[2])
    bottom=int(box[1]+box[3])
    # print(left,top,right,bottom)
    cv2.rectangle(img,(left,top),(right,bottom),color,thickness=thick)

def blur_face(img,box):
    left=int(box[0])
    top=int(box[1])
    width=int(box[2])
    height=int(box[3])
    if (len(img.shape))<3:
        pass
    face_to_blur=img[top:top+height,left:left+width,0:3]
    blur=cv2.blur(face_to_blur,(25,25))
    img[top:top+height,left:left+width,0:3]=blur

def change_yolo_to_left_top(box_from_yolo,rgb_shape,resized_shape):
    x_ratio=rgb_shape[1]/resized_shape[0]
    y_ratio=rgb_shape[0]/resized_shape[1]
    center_x=box_from_yolo[0]
    center_y=box_from_yolo[1]
    width = box_from_yolo[2]
    height = box_from_yolo[3]
    left = (center_x-width/2)
    top = (center_y-height/2)
    box_after_adjust=[0,0,0,0]
    box_after_adjust[0]=left*x_ratio
    box_after_adjust[1]=top*y_ratio
    box_after_adjust[2]=width*x_ratio
    box_after_adjust[3]=height*y_ratio
    if box_after_adjust[1]<0:
        box_after_adjust[1]=1
    if box_after_adjust[0]<0:
        box_after_adjust[0]=1
    # print(box_after_adjust)
    return box_after_adjust

def store_faces_location(boxes_from_yolo,ir_shape,rgb_shape,resized_shape,offset):
    coordinates_of_faces=[]
    number_of_head=len(boxes_from_yolo)
    for i in range(number_of_head):
            box=change_yolo_to_left_top(boxes_from_yolo[i][2],rgb_shape,resized_shape)  
            width_ratio=ir_shape[1]/rgb_shape[1]
            height_ratio=ir_shape[0]/rgb_shape[0]
            left = int(box[0]*width_ratio)+offset['x']
            top = int(box[1]*height_ratio)+offset['y']
            width = int(box[2]*width_ratio)
            height = int(box[3]*height_ratio)
            if left<0:
                left=0
            if top<0:
                top=0
            box_for_IR=[left,top,width,height]
            coordinates_of_faces.append(box_for_IR)
    # print(coordinates_of_faces)
    return coordinates_of_faces