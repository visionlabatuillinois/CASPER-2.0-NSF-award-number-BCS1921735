
# graphical run for the attention model, version 1      2/4/19

try:
    import pygame, sys, math  # , AttentionModel1, MainInterface
    from pygame.locals import *

    GRAPHICS_FAILED = False
except:
    print
    print( '* * * * * * * * * * * * * * * * * *')
    print( 'Graphics failed to load: No pygame.')
    print( '* * * * * * * * * * * * * * * * * *')
    print
    GRAPHICS_FAILED = True
    # self.parent.graphics_failed = True
    # write a file telling program that pygame has failed




# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * Not a complete interface, just a single run * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class GraphicalRun(object):
    """
    The graphical interface for the Attention Model
    """

    def __init__(self, main_interface, height=1000, width=1000):

        self.model   = main_interface.model
        self.parent  = main_interface # the main (non-graphical) interface is the parent of this one
        self.VERBOSE = False

        self.wait = True  # wait for user to keypress between iterations

        # try:
        #     import pygame, sys  # , AttentionModel1, MainInterface
        #     from pygame.locals import *
        # except:
        #     print
        #     print( '* * * * * * * * * * * * * * * * * *')
        #     print( 'Graphics failed to load: No pygame.')
        #     print( '* * * * * * * * * * * * * * * * * *')
        #     print
        #     self.parent.graphics_failed = True
        #     return None

    # def set_up_graphics(self):
        """
        sets up pygame, etc.
        :return: 
        """
        '''
        try:
            import pygame, sys  # , AttentionModel1, MainInterface
            from pygame.locals import *
        except:
            print( 'Graphics failed to load: No pygame.')
            return False
        '''


        # from pygame import *
        #
        # Define colors
        self.WHITE = (255, 255, 255)
        self.LIGHTGRAY = (250, 250, 250)
        self.GRAY = (196, 196, 196)
        self.MIDDLEGRAY = (128, 128, 128)
        self.DARKGRAY = (48, 48, 48)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.CYAN = (0, 255, 255)
        self.LIGHTBLUE = (100, 175, 255)
        self.BLUE = (50, 150, 255)
        self.DARKBLUE = (0, 0, 150)
        self.GREEN = (0, 255, 0)
        self.MIDDLEGREEN = (16, 160, 64)
        self.EASYRED = (200, 64, 64)
        self.PURPLE = (200, 16, 200)
        self.LIGHTGREEN = (50, 255, 50)
        self.YELLOW = (255, 255, 50)
        self.ORANGE = (255, 96, 0)
        self.BROWN = (155, 30, 0)

        try:
            pygame.init()
            #
            # screen set-up
            # infoObject = pygame.display.Info()
            self.screen_width = width# infoObject.current_w - 100 #1800 # 1024
            self.screen_height = height# infoObject.current_h - 100#1200 # 768
            self.large_text_height = 36
            self.small_text_height = 18
            self.med_text_height = 24
            #
            self.vert_midline = int(round(self.screen_width / 2))  # the vertical midline
            self.horiz_midline = int(round(self.screen_height / 2))
            #
            # pygame.display.set_mode((infoObject.current_w, infoObject.current_h))
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self.largefont = pygame.font.SysFont('futura', self.large_text_height)
            self.smallfont = pygame.font.SysFont('futura', self.small_text_height)
            self.medfont = pygame.font.SysFont('futura', self.med_text_height)
            pygame.mouse.set_visible(True)
            pygame.font.init()
            #
            self.parent.GRAPHIC = True
            print
            print( '* * * * * * * * * * *')
            print( 'Graphics initialized')
            print( '* * * * * * * * * * *')
            print
        except:
            print
            print( '* * * * * * * * * * * * * * * * * *')
            print( 'Graphics failed to init: No pygame.')
            print( '* * * * * * * * * * * * * * * * * *')
            print
            self.parent.graphics_failed = True
            return None

    def init_display(self):
        # if you haven't initialized the graphics yet, the do so
        # self.set_up_graphics()
        self.screen.fill(self.LIGHTGRAY)
        pygame.display.update()

    def close_display(self):
        # kill the graphics
        pygame.display.quit()
        pygame.quit()

    def draw_item(self, item, rejected_list):
        """
        dtaws a visual item
        :param item: 
        rejectedLlist is a boolean that is true if this function is called on units in the relected list
        :return: 
        """

        # draw rejected items in gray, others in their own color
        if item.rejected or rejected_list:
            color = self.GRAY
        else:
            if item.color == 'red':
                color = self.RED
            elif item.color == 'green':
                color = self.GREEN
            else:
                color = self.BROWN

        # draw everything within the rectangle self.location[0],self.location[1],ITEM_RADIUS*2,ITEM_RADIUS*2
        # WHAT you draw depends on the item's shape
        if item.shape == 'vertical':
            # a vertical line through the middle of the rectangle
            x1 = item.location[0] + self.model.ITEM_RADIUS
            x2 = x1
            y1 = item.location[1]
            y2 = item.location[1] + 2 * self.model.ITEM_RADIUS
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 3)
        elif item.shape == 'horizontal':
            # a horizontal line through the middle of the rectangle
            x1 = item.location[0]
            x2 = item.location[0] + 2 * self.model.ITEM_RADIUS
            y1 = item.location[1] + self.model.ITEM_RADIUS
            y2 = y1
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 3)
        else:
            # DIAG
            print( 'No Shape!')

            location = (item.location[0] + self.model.ITEM_RADIUS, item.location[1] + self.model.ITEM_RADIUS)
            # draw a filled circle if nothing else
            pygame.draw.circle(self.screen, color, location, self.model.ITEM_RADIUS, 0)

        # draw black circle around currently selected, light gray (background color) around everything else
        location = (item.location[0] + self.model.ITEM_RADIUS, item.location[1] + self.model.ITEM_RADIUS)

        if item == self.model.found_target: # when the item is identified as the target, turn the selection circle yellow
            color = self.PURPLE
            thickness = 4
        elif item == self.model.selected_item: # item.currently_selected:
            color = self.BLACK
            thickness = 1
        else:
            color = self.LIGHTGRAY
            thickness = 1
        pygame.draw.circle(self.screen, color, location, self.model.ITEM_RADIUS + 1, thickness)

    def show_state(self):
        """
        graphically show the state of the model with rejected items in gray
        wait means ask the user for a keypress before moving on
        :return: 
        """
        # show the search window
        if self.model.CARTESIAN_GRID:
            # draw a square
            x1 = self.model.DISPLAY_CENTER[0] - self.model.DISPLAY_RADIUS
            y1 = self.model.DISPLAY_CENTER[1] - self.model.DISPLAY_RADIUS
            width = height = 2 * self.model.DISPLAY_RADIUS
            rect = (x1, y1, width, height)
            pygame.draw.rect(self.screen, self.BLACK, rect, 1)
        else:
            # craw a circle
            pygame.draw.circle(self.screen, self.BLACK, self.model.DISPLAY_CENTER, self.model.DISPLAY_RADIUS, 1)

        # show the iteration
        self.blit_text(str(self.model.iteration))

        # show the items
        for item in self.model.search_items:
            self.draw_item(item, False) # False means Not from the rejected list
        for item in self.model.rejected_items:
            self.draw_item(item, True) # True means From the rejected list

        pygame.display.update()

        if self.wait:
            self.get_keypress()

    def show_messages(self):
        # get any mesages form the attention model and show them immediately
        pass
        #ToDo: write this routine using the graphical tools
        # for message in self.model.messages:
        #     print( message)

    def blit_text(self, message, line=1, column=1, color=None, size=None):
        # formats, renders and blits a message to screen on the designated line
        #   but does NOT update the screen.
        # it is for use in cases where it is necessary to put several lines of
        #   text on the screen
        # 1) render the message
        if color == None:
            color = self.BLUE
        if size == None:
            size = self.large_text_height
        if size == self.large_text_height:
            the_text = self.largefont.render(message, True, color, self.LIGHTGRAY)
        else:
            the_text = self.smallfont.render(message, True, color, self.LIGHTGRAY)
        # 2) set it's location
        text_rect = [column * size / 2, line * size + 5, self.screen_width, size]
        # 3) blit it to the screen
        self.screen.blit(the_text, text_rect)
        pygame.display.update()

    def get_keypress(self, trigger=None):
        # it waits for the user to enter a key in order to move on
        # NOTE: pygame.key.name() always returns the lower case version of the key; integers 0...9 are seen as chars, not ints
        all_done = False
        while not all_done:
            event_list = pygame.event.get()
            for event in event_list:
                # process the_event according to what type of event it is
                if event.type == pygame.QUIT:
                    sys.exit(0)
                    # return pygame.key.name(abort_experiment())
                elif event.type == pygame.KEYDOWN:
                    # DIAG
                    # print( pygame.key.name(event.key)+', val = '+str(event.key))
                    if type(pygame.key.name(event.key)) == int:
                        print( 'is an integer')
                    # end DIAG
                    if event.key == pygame.K_ESCAPE:
                        sys.exit(0)
                        # abort_experiment()
                    elif pygame.key.name(event.key) == trigger:
                        all_done = True
                    elif trigger == None:
                        # if there's no trigger, then assume that the program
                        # wants to know what the user entered
                        all_done = True
                        return pygame.key.name(event.key)


    def show_graphs(self, summary_rts = []):
        pres_abs_toggle = True
        maxRT = 0.0
        minRT = 0.0
        maxDists = None
        minDists = 0.0
        for suite in summary_rts:
            for condition in suite:
                for datapoint in condition[1]:
                # format is [self.model.num_lures, rt_mean, rt_sem, num_errors])
                #if not regression[-1]:              # no errors -- not sure this is necessary

                    #if not minRT:
                    #    minRT = datapoint[1]
                    if datapoint[1] > maxRT: maxRT = datapoint[1]
                    #elif datapoint[1] < minRT: minRT= datapoint[1]
                    if not maxDists:
                        maxDists = datapoint[0]
                    elif datapoint[0] > maxDists: maxDists = datapoint[0]
                    if not minDists:
                        minDists = datapoint[0]
                    elif datapoint[0] < minDists: minDists = datapoint[0]
        upperBound = int(math.ceil(maxRT/10))*10
        if upperBound > 50: ydivisions = 10
        else: ydivisions = 5

        buffer = 50
        width = 800
        height = 600
        rect = (0, 0, width, height)

        for suite in summary_rts:
            self.screen.fill(self.LIGHTGRAY)
            pygame.draw.rect(self.screen, self.BLACK, rect, 1)
            pygame.draw.line(self.screen, self.MIDDLEGRAY, (buffer, buffer), (buffer, height - buffer), 3)
            pygame.draw.line(self.screen, self.MIDDLEGRAY, (buffer, height - buffer), (width - buffer, height - buffer), 3)
            yscalingfactor = (height - 2 * buffer) / upperBound
            xscalingfactor = (width - 2 * buffer) / maxDists

            ymarker = height - buffer - ydivisions * yscalingfactor
            ylabel = ydivisions
            while ymarker > buffer:
                pygame.draw.line(self.screen, self.GRAY, (buffer + 10, ymarker), (width - buffer, ymarker), 1)
                yaxis_text = self.smallfont.render(str(ylabel), True, self.MIDDLEGRAY, self.LIGHTGRAY)
                # 2) set it's location
                yaxistext_rect = [buffer - 40, ymarker - 10, 30, self.large_text_height]
                ymarker -= ydivisions * yscalingfactor
                ylabel += ydivisions

                # 3) blit it to the screen
                self.screen.blit(yaxis_text, yaxistext_rect)

            for condition in suite:
                if  pres_abs_toggle == False:        # Target is absent


                    # For John
                    yaxis_text = self.smallfont.render(str(ylabel), True, self.MIDDLEGRAY, self.LIGHTGRAY)
                    # 2) set it's location
                    yaxistext_rect = [buffer - 40, ymarker - 10, 30, self.large_text_height]
                    self.screen.blit(yaxis_text, yaxistext_rect)

                    color = self.DARKBLUE
                    legend_text = self.smallfont.render("Absent", True, self.BLACK, self.LIGHTGRAY)
                    legend_rect = (width-2*buffer, buffer/2, width, buffer)
                    self.screen.blit(legend_text, legend_rect)
                    pygame.draw.circle(self.screen, color, (int(width - 2*buffer - 10), int(buffer / 2) + 5), 6)

                else:
                    color = self.ORANGE
                    pygame.draw.circle(self.screen, color, (int(width - 2*buffer - 10), int(buffer / 2) + 20), 6)
                    legend_text = self.smallfont.render("Present", True, self.BLACK, self.LIGHTGRAY)
                    legend_rect = (width - 2*buffer, int(buffer / 2)+15, width, buffer+20)
                    self.screen.blit(legend_text, legend_rect)
                    title_text = self.medfont.render(str(condition[0]), True, self.BLACK, self.LIGHTGRAY)
                    title_rect = [buffer, buffer / 2, width - 5*buffer, 3*buffer]


                    self.screen.blit(title_text, title_rect)
                #Draw points on graph and put on x-axis marks
                for pointindex in range(len(condition[1])):
                    pygame.draw.circle(self.screen, color, (int(buffer + int(round(condition[1][pointindex][0])*xscalingfactor)), int(height-buffer-int(round(condition[1][pointindex][1]))*yscalingfactor)), 6)
                    xaxis_text = self.smallfont.render(str(condition[1][pointindex][0]), True, self.MIDDLEGRAY,
                                                       self.LIGHTGRAY)
                    xaxistext_rect = [int(buffer + round(condition[1][pointindex][0] * xscalingfactor)),
                                      height - buffer + 20, 30, self.large_text_height]
                    self.screen.blit(xaxis_text, xaxistext_rect)

                #Draw lines in between points
                for pointindex in range(len(condition[1])-1):
                    pygame.draw.line(self.screen, color, (int(buffer + int(round(condition[1][pointindex][0])*xscalingfactor)), int(height-buffer-int(round(condition[1][pointindex][1]))*yscalingfactor)), (int(buffer + int(round(condition[1][pointindex+1][0])*xscalingfactor)), int(height-buffer-int(round(condition[1][pointindex+1][1]))*yscalingfactor)),3)


                pres_abs_toggle = not pres_abs_toggle

                pygame.display.update()
            self.get_keypress()
            #TODO: The below is wrong wrong wrong. This is what we need to make the legend, not the filename
            pygame.image.save(self.screen, str(condition[0]) + ".png")

    def show_present_graphs(self, summary_rts=[]):
        pres_abs_toggle = True
        maxRT = 0.0
        minRT = 0.0
        maxDists = None
        minDists = 0.0
        for suite in summary_rts:
            for condition in suite:
                for datapoint in condition[1]: #present vs absent
                    # format is [self.model.num_lures, rt_mean, rt_sem, num_errors])
                    # if not regression[-1]:              # no errors -- not sure this is necessary

                    # if not minRT:
                    #    minRT = datapoint[1]
                    if datapoint[1] > maxRT: maxRT = datapoint[1]
                    # elif datapoint[1] < minRT: minRT= datapoint[1]
                    if not maxDists:
                        maxDists = datapoint[0]
                    elif datapoint[0] > maxDists:
                        maxDists = datapoint[0]
                    if not minDists:
                        minDists = datapoint[0]
                    elif datapoint[0] < minDists:
                        minDists = datapoint[0]
        upperBound = int(math.ceil(maxRT / 10)) * 10
        if upperBound > 50:
            ydivisions = 10
        else:
            ydivisions = 5

        buffer = 50
        width = 800
        height = 600
        rect = (0, 0, width, height)

        for suite in summary_rts:
            self.screen.fill(self.LIGHTGRAY)
            pygame.draw.rect(self.screen, self.BLACK, rect, 1)
            pygame.draw.line(self.screen, self.MIDDLEGRAY, (buffer, buffer), (buffer, height - buffer), 3)
            pygame.draw.line(self.screen, self.MIDDLEGRAY, (buffer, height - buffer), (width - buffer, height - buffer),
                             3)
            yscalingfactor = (height - 2 * buffer) / upperBound
            xscalingfactor = (width - 2 * buffer) / maxDists

            ymarker = height - buffer - ydivisions * yscalingfactor
            ylabel = ydivisions
            while ymarker > buffer:
                pygame.draw.line(self.screen, self.GRAY, (buffer + 10, ymarker), (width - buffer, ymarker), 1)
                yaxis_text = self.smallfont.render(str(ylabel), True, self.MIDDLEGRAY, self.LIGHTGRAY)
                # 2) set it's location
                yaxistext_rect = [buffer - 40, ymarker - 10, 30, self.large_text_height]
                ymarker -= ydivisions * yscalingfactor
                ylabel += ydivisions

                # 3) blit it to the screen
                self.screen.blit(yaxis_text, yaxistext_rect)

            for condition in suite:
                if pres_abs_toggle == False:  # Target is absent

                    # For John
                    yaxis_text = self.smallfont.render(str(ylabel), True, self.MIDDLEGRAY, self.LIGHTGRAY)
                    # 2) set it's location
                    yaxistext_rect = [buffer - 40, ymarker - 10, 30, self.large_text_height]
                    self.screen.blit(yaxis_text, yaxistext_rect)

                    color = self.DARKBLUE
                    legend_text = self.smallfont.render("Absent", True, self.BLACK, self.LIGHTGRAY)
                    legend_rect = (width - 2 * buffer, buffer / 2, width, buffer)
                    self.screen.blit(legend_text, legend_rect)
                    pygame.draw.circle(self.screen, color, (int(width - 2 * buffer - 10), int(buffer / 2) + 5), 6)

                else:
                    color = self.ORANGE
                    pygame.draw.circle(self.screen, color, (int(width - 2 * buffer - 10), int(buffer / 2) + 20), 6)
                    legend_text = self.smallfont.render("Present", True, self.BLACK, self.LIGHTGRAY)
                    legend_rect = (width - 2 * buffer, int(buffer / 2) + 15, width, buffer + 20)
                    self.screen.blit(legend_text, legend_rect)
                    title_text = self.medfont.render(str(condition[0]), True, self.BLACK, self.LIGHTGRAY)
                    title_rect = [buffer, buffer / 2, width - 5 * buffer, 3 * buffer]

                    self.screen.blit(title_text, title_rect)
                # Draw points on graph and put on x-axis marks
                for pointindex in range(len(condition[1])):
                    pygame.draw.circle(self.screen, color, (
                    int(buffer + int(round(condition[1][pointindex][0]) * xscalingfactor)),
                    int(height - buffer - int(round(condition[1][pointindex][1])) * yscalingfactor)), 6)
                    xaxis_text = self.smallfont.render(str(condition[1][pointindex][0]), True, self.MIDDLEGRAY,
                                                       self.LIGHTGRAY)
                    xaxistext_rect = [int(buffer + round(condition[1][pointindex][0] * xscalingfactor)),
                                      height - buffer + 20, 30, self.large_text_height]
                    self.screen.blit(xaxis_text, xaxistext_rect)

                # Draw lines in between points
                for pointindex in range(len(condition[1]) - 1):
                    pygame.draw.line(self.screen, color, (
                    int(buffer + int(round(condition[1][pointindex][0]) * xscalingfactor)),
                    int(height - buffer - int(round(condition[1][pointindex][1])) * yscalingfactor)), (
                                     int(buffer + int(round(condition[1][pointindex + 1][0]) * xscalingfactor)), int(
                                         height - buffer - int(
                                             round(condition[1][pointindex + 1][1])) * yscalingfactor)), 3)

                pres_abs_toggle = not pres_abs_toggle

                pygame.display.update()
            self.get_keypress()
            # TODO: The below is wrong wrong wrong. This is what we need to make the legend, not the filename
            pygame.image.save(self.screen, str(condition[0]) + ".png")

    # * * * * * * * * * * * * * * *  * * *
    # * * * Simulation Running Stuff * * *
    # * * * * * * * * * * * * * * *  * * *

    def run(self, verbose_title=''):
        """
        runs the model with graphics
        :return: 
        """
        # clear the display and, if necessary, set up the graphics
        self.init_display()

        # init the state of the search
        self.model.init_search(verbose_title)

        # run the iterations until the model is done
        all_done = False
        while not all_done:
            all_done = self.model.run_search_step()
            self.show_state()

         # at the end, report the RT, whether correct, etc.
         #ToDo: rewrite this to work with graphics
         # if self.VERBOSE:
         #     for line in self.model.messages:
         #         print( line)

