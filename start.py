import ipywidgets as ipw

def get_start_widget(appbase, jupbase):
    #http://fontawesome.io/icons/
    template = """
    Requires a Computer & Code configured for running VASP.
    <table>
    <td valign="top"><ul>
    <li><a href="{appbase}/VASP-Demo.ipynb" target="_blank">Bandstructure Workflow</a>
    <li><a href="{appbase}/Workchain Monitor.ipynb" target="_blank">Monitor Workflows</a>
    </ul></td>
    </tr></table>
"""
    
    html = template.format(appbase=appbase, jupbase=jupbase)
    return ipw.HTML(html)
    
#EOF