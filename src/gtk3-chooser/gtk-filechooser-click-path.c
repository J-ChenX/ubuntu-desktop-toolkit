/* Local GTK 3 module. Uses the chooser's own Ctrl+L action, no key injection.
 * GTK 3.24 template names are checked before attaching; GTK 4 is unaffected.
 */
#include <gtk/gtk.h>
#include <gmodule.h>

static GObject *child(GtkWidget *chooser, const char *name)
{
    return gtk_widget_get_template_child(chooser, GTK_TYPE_FILE_CHOOSER_WIDGET, name);
}

static gboolean supports_click(GtkWidget *chooser)
{
    GtkFileChooserAction action = gtk_file_chooser_get_action(GTK_FILE_CHOOSER(chooser));
    return action == GTK_FILE_CHOOSER_ACTION_OPEN || action == GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER;
}

static void toggle(GtkWidget *chooser)
{
    g_signal_emit_by_name(chooser, "location-toggle-popup");
}

static void current_path_clicked(GtkWidget *bar, GFile *file,
                                 GFile *child_file, gboolean hidden,
                                 GtkWidget *chooser)
{
    (void) child_file;
    (void) hidden;
    if (!supports_click(chooser)) return;
    GFile *current = gtk_file_chooser_get_current_folder_file(GTK_FILE_CHOOSER(chooser));
    gboolean same = current && g_file_equal(current, file);
    g_clear_object(&current);
    if (same) {
        /* The built-in path-clicked callback is connected AFTER. Avoid a
         * redundant folder reload, and preserve ancestor navigation unchanged. */
        g_signal_stop_emission_by_name(bar, "path-clicked");
        toggle(chooser);
    }
}

static gboolean blank_area_event(GtkWidget *box, GdkEventButton *event, GtkWidget *chooser)
{
    if (event->button != GDK_BUTTON_PRIMARY || !supports_click(chooser)) return FALSE;
    GtkWidget *bar = GTK_WIDGET(child(chooser, "browse_path_bar"));
    gint origin_x, origin_y, box_x, box_y;
    GtkWidget *top = gtk_widget_get_toplevel(box);
    gdk_window_get_origin(gtk_widget_get_window(top), &origin_x, &origin_y);
    if (!gtk_widget_translate_coordinates(box, top, 0, 0, &box_x, &box_y)) return FALSE;
    gdouble local_x = event->x_root - origin_x - box_x;
    gdouble local_y = event->y_root - origin_y - box_y;
    GList *buttons = gtk_container_get_children(GTK_CONTAINER(bar));
    gboolean blank = local_x >= 0 && local_y >= 0 &&
                     local_x < gtk_widget_get_allocated_width(box) &&
                     local_y < gtk_widget_get_allocated_height(box);
    for (GList *p = buttons; p; p = p->next) {
        GtkWidget *button = p->data;
        gint x, y;
        if (gtk_widget_get_mapped(button) &&
            gtk_widget_translate_coordinates(button, box, 0, 0, &x, &y) &&
            local_x >= x && local_x < x + gtk_widget_get_allocated_width(button) &&
            local_y >= y && local_y < y + gtk_widget_get_allocated_height(button)) {
            blank = FALSE;
            break;
        }
    }
    g_list_free(buttons);
    if (event->type == GDK_BUTTON_PRESS) {
        g_object_set_data(G_OBJECT(box), "click-path-pressed", GINT_TO_POINTER(blank));
        return blank;
    }
    gboolean pressed = GPOINTER_TO_INT(g_object_get_data(G_OBJECT(box), "click-path-pressed"));
    g_object_set_data(G_OBJECT(box), "click-path-pressed", NULL);
    if (blank && pressed) {
        toggle(chooser);
        return TRUE;
    }
    return FALSE;
}

static void back_clicked(GtkButton *button, GtkWidget *chooser)
{
    (void) button;
    if (!supports_click(chooser)) return;
    GtkWidget *box = GTK_WIDGET(child(chooser, "location_entry_box"));
    GList *widgets = gtk_container_get_children(GTK_CONTAINER(box));
    for (GList *p = widgets; p; p = p->next)
        if (GTK_IS_ENTRY(p->data)) gtk_widget_grab_focus(p->data);
    g_list_free(widgets);
    /* Ctrl+L returns to breadcrumbs only when the location entry is focused. */
    toggle(chooser);
}

static void attach(GtkWidget *chooser)
{
    if (g_object_get_data(G_OBJECT(chooser), "click-path-attached")) return;
    GObject *bar = child(chooser, "browse_path_bar");
    GObject *entry_box = child(chooser, "location_entry_box");
    if (!GTK_IS_CONTAINER(bar) || !GTK_IS_BOX(entry_box) ||
        !g_signal_lookup("path-clicked", G_OBJECT_TYPE(bar))) return;
    GtkWidget *parent = gtk_widget_get_parent(GTK_WIDGET(bar));
    if (!GTK_IS_BOX(parent)) return;
    g_object_set_data(G_OBJECT(chooser), "click-path-attached", GINT_TO_POINTER(1));
    g_signal_connect_object(bar, "path-clicked", G_CALLBACK(current_path_clicked), chooser, 0);

    /* GtkPathBar owns an input window spanning the full allocated width.
     * Use it directly; no widget reparenting or layout change is needed. */
    gtk_widget_add_events(GTK_WIDGET(bar), GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK);
    g_signal_connect_object(bar, "button-press-event", G_CALLBACK(blank_area_event), chooser, 0);
    g_signal_connect_object(bar, "button-release-event", G_CALLBACK(blank_area_event), chooser, 0);

    GtkWidget *back = gtk_button_new_from_icon_name("go-previous-symbolic", GTK_ICON_SIZE_BUTTON);
    gtk_widget_set_name(back, "click-path-back");
    gtk_widget_set_tooltip_text(back, "返回面包屑路径（Ctrl+L）");
    atk_object_set_name(gtk_widget_get_accessible(back), "返回面包屑路径");
    gtk_widget_set_focus_on_click(back, FALSE);
    gtk_box_pack_end(GTK_BOX(entry_box), back, FALSE, FALSE, 0);
    g_signal_connect_object(back, "clicked", G_CALLBACK(back_clicked), chooser, 0);
    gtk_widget_show(back);
}

static gboolean map_hook(GSignalInvocationHint *hint, guint n, const GValue *values, gpointer data)
{
    (void) hint; (void) n; (void) data;
    GtkWidget *widget = g_value_get_object(values);
    if (GTK_IS_FILE_CHOOSER_WIDGET(widget)) attach(widget);
    return TRUE;
}

static void attach_existing(GtkWidget *widget, gpointer data)
{
    (void) data;
    if (GTK_IS_FILE_CHOOSER_WIDGET(widget)) attach(widget);
    else if (GTK_IS_CONTAINER(widget)) gtk_container_foreach(GTK_CONTAINER(widget), attach_existing, NULL);
}

G_MODULE_EXPORT void gtk_module_init(gint *argc, gchar ***argv)
{
    (void) argc; (void) argv;
    static gboolean initialized;
    if (initialized) return;
    initialized = TRUE;
    gpointer widget_class = g_type_class_ref(GTK_TYPE_WIDGET);
    g_signal_add_emission_hook(g_signal_lookup("map", GTK_TYPE_WIDGET), 0, map_hook, NULL, NULL);
    g_type_class_unref(widget_class);
    GList *windows = gtk_window_list_toplevels();
    g_list_foreach(windows, (GFunc) attach_existing, NULL);
    g_list_free(windows);
}

/* Signal hooks can outlive a GtkSettings module-list change. Keep code mapped
 * until the process exits, as GTK modules with registered callbacks require. */
G_MODULE_EXPORT const gchar *g_module_check_init(GModule *module)
{
    const gchar *error = gtk_check_version(3, 24, 0);
    if (error) return error;
    g_module_make_resident(module);
    return NULL;
}
