import cv2

class DilationVideoWriter():

    def __init__(self,
                 output_file,
                 codec,
                 frame_rate,
                 frame_shape,
                 frame_window):
        
        self.frame_window = frame_window
        
        self.interval = 10
        self.latch_count = 0

        self.out = cv2.VideoWriter(output_file,
                                   codec,
                                   frame_rate,
                                   frame_shape)
        self.count = 0

        
    def update(self, frame, target_detected):
        if target_detected:
            self.interval = 1
            # any time detected restart latch_count
            self.latch_count = 0

        self.latch_count += 1    
        if self.latch_count > self.frame_window:
            self.interval = 10
            self.latch_count = 0

        self.count += 1
        if self.count >= self.interval:
            self.out.write(frame)
            self.count = 0
            
    def release(self):
        self.out.release()
