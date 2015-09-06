#include <X11/Xlib.h>
#include <X11/cursorfont.h>

#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main()
{
    Display *dpy;
    if (!(dpy = XOpenDisplay(NULL))) {
        fprintf(stderr, "Could not open display %s", getenv("DISPLAY"));
        return 1;
    }

    Cursor cursor_ptr = XCreateFontCursor(dpy, XC_left_ptr);
    Cursor cursor_bottom_right = XCreateFontCursor(dpy, XC_lr_angle);
    Cursor cursor_bottom_left = XCreateFontCursor(dpy, XC_ll_angle);
    Cursor cursor_top_right = XCreateFontCursor(dpy, XC_ur_angle);
    Cursor cursor_top_left = XCreateFontCursor(dpy, XC_ul_angle);

    XGrabButton(dpy, 1, 0, DefaultRootWindow(dpy), True, ButtonPressMask, GrabModeSync, GrabModeAsync, None, None);

    GC sel_gc = XCreateGC(dpy, DefaultRootWindow(dpy), GCFunction | GCSubwindowMode | GCLineWidth,
                          &(XGCValues) { .function = GXinvert, .subwindow_mode = IncludeInferiors, .line_width = 1 });
    if ((XGrabPointer
         (dpy, DefaultRootWindow(dpy), False,
          ButtonPressMask, GrabModeAsync,
          GrabModeAsync, DefaultRootWindow(dpy), cursor_ptr, CurrentTime) != GrabSuccess)) {
        fprintf(stderr, "Could not grab mouse\n");
        return 1;
    }

    bool grabbing = false;
    int start_x, start_y, x, y, width, height;
    while (true) {
        XEvent ev;
        XNextEvent(dpy, &ev);

        if (ev.type == ButtonPress) {
            x = start_x = ev.xbutton.x_root;
            y = start_y = ev.xbutton.y_root;

            width = height = 0;
            grabbing = true;
            XChangeActivePointerGrab(dpy, ButtonMotionMask | ButtonReleaseMask,
                                     cursor_ptr, CurrentTime);
        } else if (ev.type == MotionNotify) {
            if (grabbing) {
                // Choose cursor based on mouse position
                Cursor cur;
                if (x < start_x) {
                    if (y < start_y) cur = cursor_top_left;
                    else cur = cursor_bottom_left;
                } else {
                    if (y < start_y) cur = cursor_top_right;
                    else cur = cursor_bottom_right;
                }
                XChangeActivePointerGrab(
                        dpy, ButtonMotionMask | ButtonReleaseMask,
                        cur, CurrentTime
                );

                // Discard all but the latest MotionNotify event
                while (XCheckTypedEvent(dpy, MotionNotify, &ev));

                // Clear previous rectangle
                XDrawRectangle(dpy, DefaultRootWindow(dpy), sel_gc,
                               x, y, width, height); /* Clear Rectangle */

                width = ev.xbutton.x_root - start_x;
                height = ev.xbutton.y_root - start_y;

                /* Ugliness to make width/height positive and put the start positions
                 * in the right place so we can draw backwards basically. */
                if (width  < 0) { width  =  -width; x = ev.xbutton.x_root; } else { x = start_x; }
                if (height < 0) { height = -height; y = ev.xbutton.y_root; } else { y = start_y; }

                // Draw new rectangle
                XDrawRectangle(dpy, DefaultRootWindow(dpy), sel_gc, x, y, width, height);
            }
        } else if (ev.type == ButtonRelease) {
            XUngrabPointer(dpy, CurrentTime);

            // Clear previous recrangle
            XDrawRectangle(dpy, DefaultRootWindow(dpy), sel_gc, x, y, width, height);

            printf("%i %i %i %i\n", x, y, width, height);
            break;
        }
    }

    XFreeGC(dpy, sel_gc);
    XCloseDisplay(dpy);
    return 0;
}
