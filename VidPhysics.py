# /// script
# dependencies = ["nicegui","Pillow","numpy","opencv-python"]
# ///
import numpy as np
import cv2
from PIL import Image
from nicegui import ui,events,app
import os

__version__="0.0.3"

def mouse_handler(e: events.MouseEventArguments):

    if not demo._calibration_mode:
        color = 'red'
        demo.img_display.content += f'<circle cx="{e.image_x}" cy="{e.image_y}" r="4" fill="none" stroke="{color}" stroke-width="2" />'
        demo.locations.append( [demo.frame_number,e.image_x,e.image_y] )
        demo.next_frame()

    else:
        color = 'green'
        demo.img_display.content += f'<rect x="{e.image_x-3}" y="{e.image_y-3}" width="6" height="6" fill="none" stroke="{color}" stroke-width="2" />'
        demo._calibration_locations.append( [e.image_x,e.image_y] )

        if len(demo._calibration_locations)==2:  # done calibrating
            demo._calibration_mode=False
            demo.set_meters()

def keyboard_handler(e: events.KeyEventArguments):
    print("in key")
    if e.action.keydown:
        if e.key.arrow_left:
            demo.prev_frame()
        elif e.key.arrow_right:
            demo.next_frame()



# Add keyboard handler at the page level
ui.keyboard(on_key=keyboard_handler)



class Demo:
    def __init__(self):
        self.can_calibrate=False
        self.can_export=False
        self.can_rotate=False
        self.meters_per_pixel=None
        self._calibration_mode=False
        self._calibration_locations=[]
        self._calibration_meters=1
        self.frames=[]
        self.frame_number = 1
        self.locations=[]
        self.video_path=''
        self.current_frame=0
        self.container=''
        self.img_display=''
        self.text=''
        self.fps=30
        self.shape=''
        self.n=0
        self.empty=''

    def reject(self):
        print('Video Upload Failed')


    async def load(self,e: events.UploadEventArguments):
        from pathlib import Path
        import tempfile

        self._calibration_mode=False
        self._calibration_locations=[]
        self._calibration_meters=1

        file_extension = Path(e.file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await e.file.read())        

        print(temp_path)
        
        ui.notify(f'Uploaded {e.file.name}')

        self.frame_number = 1
        self.locations=[]
        self.video_path=f"{temp_path}"
        self.read_frames()

        self.current_frame=self.frames[self.frame_number]

        if self.shape[0]>self.shape[1]:
            style='height: 90vh;'
        else:
            style='width: 90vw;'

        self.container.clear()
        with self.container:
            self.img_display = ui.interactive_image(self.current_frame,
                                on_mouse=mouse_handler,
                                events=['mousedown',], cross=True,
                                ).style(style)
            

            
            ui.slider(min=0, max=demo.N-1).bind_value(self, 'frame_number').on('change', lambda e: self.update("this"))
            ui.number(precision=0).bind_value(self, 'frame_number').on('change', lambda e: self.update("that"))
            with ui.scroll_area().classes('border'):
                self.text=ui.label().style('white-space: pre-wrap')


        self.can_calibrate=True
        self.can_rotate=True
        self.can_export=False


        self.update()
    
    def rotate(self):
        self.read_frames("rotate")
        self.update()

    def update(self,message=None):
        if not self.frames:
            self.can_export=False
            return 
        
        self.frame_number=int(self.frame_number) # number fields convert to float
        if self.frame_number>=len(self.frames):
            self.frame_number=len(self.frames)-1
            
        self.current_frame=self.frames[self.frame_number]

        if message:
            print("Frame:",self.frame_number," of ",self.n," frames")

        if self.img_display:
            self.img_display.source=self.current_frame
            self.img_display.update()

            self.text.set_text(self.data_text)
            if self.locations:
                self.can_rotate=False
                self.can_export=True

    @property
    def data_text(self):
        if self.text and self.locations:

            t,x,y=zip(*self.locations)
            y=[self.shape[0]-_ for _ in y]

            L=len(x)
            Lv=L-1

            vx=[]
            vy=[]
            tv=[]

            if len(self._calibration_locations)==2:
                t=[frame_number/self.fps for frame_number in t]


            for i in range(Lv):
                try:
                    vx.append((x[i+1]-x[i])/(t[i+1]-t[i]))
                except ZeroDivisionError:
                    vx.append(np.nan)

                try:
                    vy.append((y[i+1]-y[i])/(t[i+1]-t[i]))
                except ZeroDivisionError:
                    vy.append(np.nan)

                tv.append((t[i+1]+t[i])/2)

            if len(self._calibration_locations)==2:  # calibrated!
                S=[]
                S.append("t [sec], x [m], y [m],   ,tv [sec],vx [m/s], vy[m/s]")
                x1,y1=self._calibration_locations[0]
                x2,y2=self._calibration_locations[1]
                meters_per_pixel=self._calibration_meters/np.sqrt((x1-x2)**2 + (y1-y2)**2)
                fps=self.fps
                dt=1/self.fps

                for i,loc in enumerate(self.locations):
                    if i<Lv:
                        S.append(f"{t[i]:.5g} , {x[i]*meters_per_pixel:.5g} , {y[i]*meters_per_pixel:.5g},     ,  {tv[i]*dt:.5g} , {vx[i]*meters_per_pixel/dt:.5g} , {vy[i]*meters_per_pixel/dt:.5g}")
                    else:
                        S.append(f"{t[i]:.5g} , {x[i]*meters_per_pixel:.5g} , {y[i]*meters_per_pixel:.5g},     ,   ,  , ")

            else:
                S=[]
                S.append("t [frames], x [pix], y [pix],   ,tv [frames],vx [pix/frame], vy[pix/frame]")
                for i,loc in enumerate(self.locations):
                    if i<Lv:
                        S.append(f"{t[i]:.0f} , {x[i]:.0f} , {y[i]:.0f},     ,  {tv[i]:.1g} , {vx[i]:.5g} , {vy[i]:.5g}")
                    else:
                        S.append(f"{t[i]:.0f} , {x[i]:.0f} , {y[i]:.0f},  ")

            S="\n".join(S)

        else:
            S=""

        return S




    def calibrate(self):
        self._calibration_mode=True
        self._calibration_locations=[]
        self._calibration_meters=1

        with ui.dialog() as dialog, ui.card():
            ui.label('After closing this dialog, click on two points separated by a known distance.')
            ui.button('Close', on_click=dialog.close)
        dialog.open()

    def set_meters(self):
        with ui.dialog() as dialog, ui.card():
            ui.label('How many meters is this?')
            new_value = ui.number(value=demo._calibration_meters,label="meters")
            
            # Button to set the variable and close the dialog
            def on_submit():
                demo._calibration_meters=new_value.value
                dialog.close()
                demo.update()
            
            ui.button('Submit', on_click=on_submit)

        dialog.open()

    def next_frame(self):
        self.frame_number+=1
        if self.frame_number>self.N:
            self.frame_number=self.N
        else:
            self.update()

    def prev_frame(self):
        self.frame_number-=1
        if self.frame_number<1:
            self.frame_number=1
        else:
            self.update()


    def read_frames(self,rotate=None):
        frames_as_pil = []  # List to hold frames as PIL images
        
        cap = cv2.VideoCapture(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)

        print("frame rate",self.fps)

        if rotate:
            print("Message:",rotate)

        while True:
            ret, frame = cap.read()  # Read next frame
            if not ret:
                break  # Break the loop if no more frames
            
            # Rotate frames by 90 degrees if requested
            if rotate:
                frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

            # Convert the frame from BGR (OpenCV format) to RGB (PIL format)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert the NumPy array (frame_rgb) to a PIL image
            pil_image = Image.fromarray(frame_rgb)
            self.shape=frame_rgb.shape
            
            # Append the PIL image to the list
            frames_as_pil.append(pil_image)

        # Release the video capture object
        cap.release()

        self.frames=frames_as_pil
        self.N=len(self.frames)
        ui.notify(f"Read {self.N} frames.")    


demo = Demo()
ui.page_title(f'Video Measurements {__version__}')
with ui.row():
    ui.upload(label="Select a Video with (+) or Drag and Drop a Video Here",
              auto_upload=True,on_upload=lambda e: demo.load(e))        

    ui.button("Rotate Video",on_click=lambda e: demo.rotate()).bind_enabled_from(demo, 'can_rotate')
    ui.button("Calibrate",on_click=lambda e: demo.calibrate()).bind_enabled_from(demo, 'can_calibrate')
    ui.button("Export csv",
                on_click=lambda e: ui.download(bytes(demo.data_text, 'utf-8'),'data.csv')).bind_enabled_from(demo, 'can_export')
    ui.number(label='Frames Per Second', value=30,
         validation={'Needs to be greater than zero': lambda value: value is not None and value > 0},
         on_change=demo.update,
         ).bind_value(demo, 'fps')
  
demo.container = ui.row() 
with demo.container:  
   empty = ui.label("No Video Chosen.")

ui.run(host="127.0.0.1")