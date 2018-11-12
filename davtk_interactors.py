import select, sys
import vtk
from davtk_parse import parse_line

class RubberbandSelect(vtk.vtkInteractorStyleRubberBand2D):
    def __init__(self,davtk_state,parent=None):
        self.AddObserver("LeftButtonReleaseEvent",self.leftButtonReleaseEvent)
        self.prev_style = None
        self.davtk_state = davtk_state

    def set_prev_style(self, prev_style):
        self.prev_style = prev_style

    def leftButtonReleaseEvent(self,obj,event):
        p0 = self.GetStartPosition()
        p1 = self.GetEndPosition()

        picker = vtk.vtkAreaPicker()
        picker.AreaPick(p0[0], p0[1], p1[0], p1[1], self.GetDefaultRenderer())
        at = self.davtk_state.cur_at()
        picked_ats = []
        for p in picker.GetProp3Ds():
            if hasattr(p,"i_at"):
                at.arrays["_vtk_picked"][p.i_at] = not at.arrays["_vtk_picked"][p.i_at] 
                picked_ats.append(p.i_at)
            else:
                raise ValueError("picked something that's not an atom "+str(p))
        self.davtk_state.update_atoms(frames="cur",atoms=picked_ats)

        self.OnLeftButtonUp()

        if self.prev_style is None:
            raise ValueError("leftButtonReleaseEvent prev_style not set")

        self.GetInteractor().SetInteractorStyle(self.prev_style)
        self.prev_style.GetInteractor().Render()
        self.prev_Style = None

        return

class MouseInteractorHighLightActor(vtk.vtkInteractorStyleTrackballCamera):

    def __init__(self,settings,davtk_state,select_style,parent=None):
        self.AddObserver("RightButtonPressEvent",self.rightButtonPressEvent)
        self.AddObserver("KeyPressEvent",self.keyPressEvent)
        self.AddObserver("TimerEvent",self.timerEvent)

        if(parent is not None):
            self.parent = parent
        else:
            self.parent = vtk.vtkRenderWindowInteractor()

        self.davtk_state = davtk_state
        self.settings = settings
        self.select_style = select_style

    def timerEvent(self,obj,event):
        if select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline()
            try:
                print "parsing line", line.rstrip()
                refresh = parse_line(line.rstrip(), self.settings, self.davtk_state, self.GetDefaultRenderer())
                if refresh == "all":
                    self.davtk_state.update()
                elif refresh == "cur":
                    self.davtk_state.update(frames="cur")
                elif refresh is not None:
                    raise ValueError("unknown refresh type "+str(refresh))
            except Exception, e:
                print "error parsing line",str(e)

            if self.GetInteractor() is not None:
                self.GetInteractor().Render()
            self.GetDefaultRenderer().GetRenderWindow().Render()

    def keyPressEvent(self,obj,event):
        k = self.parent.GetKeySym()
        if k == 's':
            self.GetInteractor().SetInteractorStyle(self.select_style)
            self.select_style.set_prev_style(self)
        elif k == 'd':
            self.davtk_state.delete(atoms="picked", frames="cur")
        elif k == 'm':
            self.davtk_state.measure_picked()
        elif k == 'plus':
            self.davtk_state.set_shown_frame(dframe=1)
        elif k == 'minus':
            self.davtk_state.set_shown_frame(dframe=-1)
        # elif k == 'c':
            # if select.select([sys.stdin,],[],[],0.0)[0]:
                # print "Have data!"
            # else:
                # print "No data"

        if self.GetInteractor() is not None:
            self.GetInteractor().Render()
        self.GetDefaultRenderer().GetRenderWindow().Render()

        # self.OnKeyPress()
        return

    def rightButtonPressEvent(self,obj,event):
        # get the actor at the picked position

        clickPos = self.GetInteractor().GetEventPosition()
        picker = vtk.vtkPropPicker()
        picker.Pick(clickPos[0], clickPos[1], 0, self.GetDefaultRenderer())
        self.NewPickedActor = picker.GetActor()

        # If something was selected
        at = self.davtk_state.cur_at()
        picked_ats = []
        if self.NewPickedActor:
            if hasattr(self.NewPickedActor,"i_at"):
                at.arrays["_vtk_picked"][self.NewPickedActor.i_at] = not at.arrays["_vtk_picked"][self.NewPickedActor.i_at] 
                picked_ats.append(self.NewPickedActor.i_at)
            else:
                raise ValueError("picked something that's not an atom "+str(self.NewPickedActor))
        self.davtk_state.update_atoms(frames="cur",atoms=picked_ats)

        self.GetInteractor().Render()

        self.OnRightButtonDown()
        return
