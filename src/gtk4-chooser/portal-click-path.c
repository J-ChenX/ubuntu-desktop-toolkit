/* Scoped GTK 4 portal patch. Loaded only by xdg-desktop-portal-gnome.
 * The portal explicitly calls gtk_widget_realize() on each chooser dialog.
 * Preserve that call and attach the native location-toggle-popup action. */
#define _GNU_SOURCE
#include <gtk/gtk.h>
#include <dlfcn.h>

static GObject *part(GtkWidget *chooser, const char *name)
{
    return gtk_widget_get_template_child(chooser, GTK_TYPE_FILE_CHOOSER_WIDGET, name);
}

static gboolean editable_action(GtkWidget *chooser)
{
    GtkFileChooserAction action = gtk_file_chooser_get_action(GTK_FILE_CHOOSER(chooser));
    return action == GTK_FILE_CHOOSER_ACTION_OPEN || action == GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER;
}

static void open_current_location(GtkWidget *chooser)
{
    /* Capture the directory before GTK updates the entry/selection. A selected
     * file must not replace the current folder address. get_parse_name keeps
     * local paths readable and represents remote folders as parseable URIs. */
    GFile *folder = gtk_file_chooser_get_current_folder(GTK_FILE_CHOOSER(chooser));
    gchar *address = folder ? g_file_get_parse_name(folder) : NULL;
    g_clear_object(&folder);
    g_signal_emit_by_name(chooser, "location-toggle-popup");
    GtkStack *stack = GTK_STACK(part(chooser, "browse_header_stack"));
    if (address && g_strcmp0(gtk_stack_get_visible_child_name(stack), "location") == 0) {
        GtkWidget *box = GTK_WIDGET(part(chooser, "location_entry_box"));
        for (GtkWidget *w = gtk_widget_get_first_child(box); w; w = gtk_widget_get_next_sibling(w)) {
            if (GTK_IS_EDITABLE(w)) {
                gtk_editable_set_text(GTK_EDITABLE(w), address);
                gtk_widget_grab_focus(w);
                gtk_editable_select_region(GTK_EDITABLE(w), 0, -1);
                break;
            }
        }
    }
    g_free(address);
}

static void path_clicked(GtkWidget *bar, GFile *file, GFile *child,
                         gboolean hidden, GtkWidget *chooser)
{
    (void) child; (void) hidden;
    if (!editable_action(chooser)) return;
    GFile *current = gtk_file_chooser_get_current_folder(GTK_FILE_CHOOSER(chooser));
    gboolean same = current && g_file_equal(current, file);
    g_clear_object(&current);
    if (same) {
        g_signal_stop_emission_by_name(bar, "path-clicked");
        open_current_location(chooser);
    }
}

static gboolean is_blank(GtkWidget *bar, double x, double y)
{
    if (x < 0 || y < 0 || x >= gtk_widget_get_width(bar) || y >= gtk_widget_get_height(bar)) return FALSE;
    GtkWidget *picked = gtk_widget_pick(bar, x, y, GTK_PICK_DEFAULT);
    for (GtkWidget *w = picked; w && w != bar; w = gtk_widget_get_parent(w))
        if (GTK_IS_BUTTON(w)) return FALSE;
    return TRUE;
}

static void blank_pressed(GtkGestureClick *gesture, int n, double x, double y, GtkWidget *chooser)
{
    (void) n;
    GtkWidget *bar = gtk_event_controller_get_widget(GTK_EVENT_CONTROLLER(gesture));
    gboolean blank = editable_action(chooser) && is_blank(bar, x, y);
    g_object_set_data(G_OBJECT(gesture), "blank-pressed", GINT_TO_POINTER(blank));
    if (blank) gtk_gesture_set_state(GTK_GESTURE(gesture), GTK_EVENT_SEQUENCE_CLAIMED);
}

static void blank_released(GtkGestureClick *gesture, int n, double x, double y, GtkWidget *chooser)
{
    (void) n;
    gboolean pressed = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(gesture), "blank-pressed"));
    g_object_set_data(G_OBJECT(gesture), "blank-pressed", NULL);
    GtkWidget *bar = gtk_event_controller_get_widget(GTK_EVENT_CONTROLLER(gesture));
    if (pressed && editable_action(chooser) && is_blank(bar, x, y)) open_current_location(chooser);
}

static void close_location(GtkWidget *chooser)
{
    if (!editable_action(chooser) ||
        g_strcmp0(gtk_stack_get_visible_child_name(GTK_STACK(part(chooser, "browse_header_stack"))), "location") != 0) return;
    GtkWidget *box = GTK_WIDGET(part(chooser, "location_entry_box"));
    for (GtkWidget *w = gtk_widget_get_first_child(box); w; w = gtk_widget_get_next_sibling(w)) {
        if (g_signal_lookup("hide-entry", G_OBJECT_TYPE(w))) {
            /* GTK 4.6 delegates focus to GtkText; Ctrl+L tests focus on the
             * outer entry. Use the entry's own Escape action to return. */
            g_signal_emit_by_name(w, "hide-entry");
            return;
        }
    }
}

static void back_clicked(GtkButton *button, GtkWidget *chooser)
{
    (void) button;
    close_location(chooser);
}

static void file_background_pressed(GtkGestureClick *gesture, int n,
                                    double x, double y, GtkWidget *chooser)
{
    if (n != 1 || !editable_action(chooser) ||
        (gtk_event_controller_get_current_event_state(GTK_EVENT_CONTROLLER(gesture)) &
         gtk_accelerator_get_default_mod_mask()) != 0) return;
    GtkStack *stack = GTK_STACK(part(chooser, "browse_header_stack"));
    if (g_strcmp0(gtk_stack_get_visible_child_name(stack), "location") != 0) return;
    GtkWidget *tree = gtk_event_controller_get_widget(GTK_EVENT_CONTROLLER(gesture));
    if (!is_blank(tree, x, y)) return; /* Exclude column header buttons. */
    gint bin_x, bin_y;
    gtk_tree_view_convert_widget_to_bin_window_coords(GTK_TREE_VIEW(tree),
                                                      (gint)x, (gint)y, &bin_x, &bin_y);
    if (bin_y < 0 || gtk_tree_view_get_path_at_pos(GTK_TREE_VIEW(tree), bin_x, bin_y,
                                                NULL, NULL, NULL, NULL)) return;
    /* Match the file manager: cancel an unsubmitted location on a plain
     * background press, then let the tree handle the event normally. */
    close_location(chooser);
    gtk_widget_grab_focus(tree);
}

static void stack_changed(GtkStack *stack, GParamSpec *pspec, GtkWidget *chooser)
{
    (void) pspec;
    if (g_strcmp0(gtk_stack_get_visible_child_name(stack), "location") != 0) return;
    GtkWidget *box = GTK_WIDGET(part(chooser, "location_entry_box"));
    GtkWidget *back = g_object_get_data(G_OBJECT(chooser), "portal-click-back");
    GtkWidget *last = gtk_widget_get_last_child(box);
    if (last != back) gtk_box_reorder_child_after(GTK_BOX(box), back, last);
}

static void attach(GtkWidget *chooser)
{
    if (g_object_get_data(G_OBJECT(chooser), "portal-click-attached")) return;
    GObject *bar = part(chooser, "browse_path_bar");
    GObject *box = part(chooser, "location_entry_box");
    GObject *stack = part(chooser, "browse_header_stack");
    GObject *tree = part(chooser, "browse_files_tree_view");
    if (!GTK_IS_WIDGET(bar) || !GTK_IS_BOX(box) || !GTK_IS_STACK(stack) || !GTK_IS_TREE_VIEW(tree) ||
        !g_signal_lookup("path-clicked", G_OBJECT_TYPE(bar))) return;
    g_object_set_data(G_OBJECT(chooser), "portal-click-attached", GINT_TO_POINTER(1));
    g_signal_connect_object(bar, "path-clicked", G_CALLBACK(path_clicked), chooser, 0);
    GtkGesture *gesture = gtk_gesture_click_new();
    gtk_gesture_single_set_button(GTK_GESTURE_SINGLE(gesture), GDK_BUTTON_PRIMARY);
    gtk_event_controller_set_propagation_phase(GTK_EVENT_CONTROLLER(gesture), GTK_PHASE_CAPTURE);
    g_signal_connect_object(gesture, "pressed", G_CALLBACK(blank_pressed), chooser, 0);
    g_signal_connect_object(gesture, "released", G_CALLBACK(blank_released), chooser, 0);
    gtk_widget_add_controller(GTK_WIDGET(bar), GTK_EVENT_CONTROLLER(gesture));

    GtkGesture *background = gtk_gesture_click_new();
    gtk_gesture_single_set_button(GTK_GESTURE_SINGLE(background), GDK_BUTTON_PRIMARY);
    gtk_event_controller_set_propagation_phase(GTK_EVENT_CONTROLLER(background), GTK_PHASE_CAPTURE);
    g_signal_connect_object(background, "pressed", G_CALLBACK(file_background_pressed), chooser, 0);
    gtk_widget_add_controller(GTK_WIDGET(tree), GTK_EVENT_CONTROLLER(background));

    GtkWidget *back = gtk_button_new_from_icon_name("go-previous-symbolic");
    gtk_widget_set_name(back, "portal-click-back");
    gtk_widget_set_tooltip_text(back, "返回面包屑路径（Ctrl+L）");
    gtk_accessible_update_property(GTK_ACCESSIBLE(back), GTK_ACCESSIBLE_PROPERTY_LABEL, "返回面包屑路径", -1);
    gtk_widget_set_focus_on_click(back, FALSE);
    gtk_box_append(GTK_BOX(box), back);
    g_object_set_data(G_OBJECT(chooser), "portal-click-back", back);
    g_signal_connect_object(back, "clicked", G_CALLBACK(back_clicked), chooser, 0);
    g_signal_connect_object(stack, "notify::visible-child-name", G_CALLBACK(stack_changed), chooser, 0);
    stack_changed(GTK_STACK(stack), NULL, chooser);
}

static void visit(GtkWidget *widget)
{
    if (GTK_IS_FILE_CHOOSER_WIDGET(widget)) attach(widget);
    else for (GtkWidget *w = gtk_widget_get_first_child(widget); w; w = gtk_widget_get_next_sibling(w)) visit(w);
}

void gtk_widget_realize(GtkWidget *widget)
{
    static void (*original)(GtkWidget *);
    if (!original) {
        original = (void (*)(GtkWidget *)) dlsym(RTLD_NEXT, "gtk_widget_realize");
        if (!original) g_error("portal-click-path: cannot resolve gtk_widget_realize");
    }
    if (GTK_IS_FILE_CHOOSER_DIALOG(widget)) visit(widget);
    original(widget);
}
