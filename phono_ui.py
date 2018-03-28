import ipywidgets as widgets
from IPython.display import display, clear_output, HTML, Javascript
from fileupload import FileUploadWidget


WARNINGSBOX = widgets.HTML("")

STYLES = [
    "background-color: rgb(242, 222, 222)",
    "border-color: rgb(235, 204, 209)",
    "border-radius: 4px",
    "border-style: solid",
    "border-width: 1px",
    "font-size: 14px",
    "line-height: 20px",
    "margin: 0px",
    "padding: 10px",
    "padding-left: 20px",
    "padding-right: 20px",
]

# An object that can be 'Display'ed to jump back here
JS_JUMP = Javascript("""window.location.href = "#warningsbox";""")


def show_warning(msg):
    """
    Shows a warning in a red box.

    If msg is empty or None, removes the box.
    :param msg: Should be a valid HTML string (this is not validated)
    """
    global WARNINGSBOX

    if not msg:
        WARNINGSBOX.value = ''
    else:
        WARNINGSBOX.value = '<div style="{}">WARNING! {}</div>'.format("; ".join(styles), msg)


def init_warnings():
    display(WARNINGSBOX)


def nice_errors(default_return=None):
    def decorator(fn):
        def inner_fn(*args, **kwargs):
            try:
                # Clean-up before running the function
                show_warning('')
                return fn(*args, **kwargs)
            except Exception as e:
                # "Eat" the exception but show an error
                show_warning("Internal error during execution. Error: {}".format(
                    str(e)))
                display(js_jump)
                return default_return
        return inner_fn
    return decorator
