import json
from datetime import datetime
from pyscript import document, window
from pyodide.ffi import create_proxy

# --- STATE MANAGEMENT ---
# In-memory state
app_state = {
    "projects": [],
    "current_filter": "all",
    "active_project_id": None,
    "task_sort": "last_added"
}

def load_data():
    """Load projects from localStorage."""
    data = window.localStorage.getItem('fernle_data')
    if data:
        try:
            app_state["projects"] = json.loads(data)
        except Exception as e:
            print(f"Error loading data: {e}")
            app_state["projects"] = []
    else:
        app_state["projects"] = []

def save_data():
    """Save projects to localStorage."""
    window.localStorage.setItem('fernle_data', json.dumps(app_state["projects"]))


# --- UI RENDERING ---

def get_time_ago(timestamp_str):
    """Calculate a simple 'time ago' string."""
    try:
        # Pyscript datetime handling can sometimes be tricky depending on the environment,
        # but standard Python ISO format works well.
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - dt
        
        days = diff.days
        seconds = diff.seconds
        
        if days > 0:
            if days == 1: return "Yesterday"
            return f"{days} days ago"
        elif seconds >= 3600:
            hours = seconds // 3600
            if hours == 1: return "1 hr ago"
            return f"{hours} hrs ago"
        elif seconds >= 60:
            minutes = seconds // 60
            if minutes == 1: return "1 min ago"
            return f"{minutes} mins ago"
        else:
            return "Just now"
    except Exception as e:
        print(f"Date error: {e}")
        return "Recently"

def render_projects():
    """Render the project list based on current state and filter."""
    container = document.getElementById("project-list")
    empty_state = document.getElementById("empty-state")
    
    # Clear current content EXCEPT the empty state which we will toggle
    for child in list(container.children):
        if child.id != "empty-state":
            child.remove()
            
    # Apply filter
    filtered_projects = app_state["projects"]
    if app_state["current_filter"] != "all":
        filtered_projects = [p for p in app_state["projects"] if p.get("category") == app_state["current_filter"]]
        
    # Sort by pinned (True first), then by updated_at (newest first)
    try:
        filtered_projects.sort(key=lambda x: (x.get("is_pinned", False), x.get("updated_at", "")), reverse=True)
    except:
        pass
        
    # Show/Hide Empty State
    if not filtered_projects:
        if empty_state: empty_state.style.display = "flex"
        update_tab_counts()
        return
    else:
        if empty_state: empty_state.style.display = "none"

    # Render Cards
    for project in filtered_projects:
        p_id = project.get("id")
        card = document.createElement("div")
        card.className = "project-card"
        card.setAttribute("onclick", f"openProject('{p_id}')")
        
        # Category Tag Logic
        cat = project.get("category", "none")
        tag_html = ""
        if cat == "work":
            tag_html = '<span class="tag tag-work">WORK</span>'
        elif cat == "personal":
            tag_html = '<span class="tag tag-personal">PERSONAL</span>'
            
        time_str = get_time_ago(project.get("updated_at", ""))
        
        # Pin Icon logic
        is_pinned = project.get("is_pinned", False)
        pin_html = '<span class="material-icons-round pin-icon" title="Pinned">push_pin</span>' if is_pinned else ''
        pin_menu_text = "Unpin Project" if is_pinned else "Pin Project"
        pin_menu_icon = "push_pin"
        
        card.innerHTML = f"""
            <div class="card-header">
                {pin_html}
                <h3 class="card-title">{project.get('name', 'Untitled')}</h3>
                {tag_html}
                <div style="position:relative;">
                    <button class="icon-btn more-btn" onclick="event.stopPropagation(); toggleDropdown('{p_id}')"><span class="material-icons-round">more_vert</span></button>
                    <!-- Dropdown Menu -->
                    <div id="dropdown-{p_id}" class="dropdown-menu" style="display:none;" onclick="event.stopPropagation();">
                        <div class="dropdown-item" onclick="togglePin('{p_id}')">
                            <span class="material-icons-round">{pin_menu_icon}</span> {pin_menu_text}
                        </div>
                        <div class="dropdown-item" onclick="openEditModal('{p_id}')">
                            <span class="material-icons-round">edit</span> Edit Project
                        </div>
                        <div class="dropdown-item dropdown-item-danger" onclick="deleteProject('{p_id}')">
                            <span class="material-icons-round">delete</span> Delete
                        </div>
                    </div>
                </div>
            </div>
            <p class="card-desc">{project.get('description', '')}</p>
            <div class="card-meta">
                <span class="meta-item"><span class="material-icons-round">history</span> Updated {time_str}</span>
            </div>
        """
        container.appendChild(card)
        
    update_tab_counts()


def update_tab_counts():
    """Update the item counts in the tabs."""
    all_count = len(app_state["projects"])
    
    # Update All tab
    all_tab = document.querySelector('.tab[data-filter="all"]')
    if all_tab:
        badge = all_tab.querySelector('.badge')
        if badge:
            badge.innerText = str(all_count)
        else:
            # Recreate badge if it doesn't exist
            if all_count > 0:
                all_tab.innerHTML = f'<span class="material-icons-round">folder</span> All <span class="badge">{all_count}</span>'
            else:
                all_tab.innerHTML = '<span class="material-icons-round">folder</span> All'


# --- EVENT HANDLERS ---

def handle_tab_click(e):
    """Filter projects when a tab is clicked."""
    # Find the closest button element in case an inner span was clicked
    target = e.target
    while target and target.tagName != 'BUTTON' and not target.classList.contains('tab'):
        target = target.parentElement
        
    if not target or not target.hasAttribute('data-filter'):
        return

    filter_val = target.getAttribute('data-filter')
    app_state["current_filter"] = filter_val
    
    # Update UI styling
    tabs = document.querySelectorAll('.tab')
    for tab in tabs:
        tab.classList.remove('active')
    target.classList.add('active')
    
    render_projects()


def open_create_modal(e):
    modal = document.getElementById("create-modal")
    if modal:
        modal.style.display = "flex"
        # Reset form
        document.getElementById("project-name").value = ""
        document.getElementById("project-desc").value = ""
        radios = document.querySelectorAll('input[name="project-category"]')
        for r in radios:
            if r.value == "none":
                r.checked = True
                
        # Focus input
        setTimeout_proxy = getattr(window, "setTimeout")
        def do_focus():
            document.getElementById("project-name").focus()
        setTimeout_proxy(create_proxy(do_focus), 100)

def close_create_modal(e):
    modal = document.getElementById("create-modal")
    if modal:
        modal.style.display = "none"

def save_new_project(e):
    name_input = document.getElementById("project-name")
    desc_input = document.getElementById("project-desc")
    
    name_val = name_input.value.strip()
    if not name_val:
        # Simple validation
        name_input.style.border = "1px solid red"
        return
        
    name_input.style.border = ""
    desc_val = desc_input.value.strip()
    
    # Get selected category
    category = "none"
    radios = document.querySelectorAll('input[name="project-category"]')
    for r in radios:
        if r.checked:
            category = r.value
            break
            
    # Create new project object (using simple dictionary for now)
    import time
    now_iso = datetime.now().isoformat()
    # Simple ID generation
    p_id = f"proj_{int(time.time() * 1000)}"
    
    new_project = {
        "id": p_id,
        "name": name_val,
        "description": desc_val,
        "category": category,
        "created_at": now_iso,
        "updated_at": now_iso,
        "is_pinned": False,
        "tasks": [],
        "custom_tags": [],
        "notes": [] # Notes will go here later
    }
    
    app_state["projects"].insert(0, new_project) # Add to top
    save_data()
    
    close_create_modal(None)
    
    # Switch to "All" tab to ensure new project is seen
    app_state["current_filter"] = "all"
    tabs = document.querySelectorAll('.tab')
    for tab in tabs:
        if tab.getAttribute('data-filter') == 'all':
            tab.classList.add('active')
        else:
            tab.classList.remove('active')
            
    render_projects()


# --- DROPDOWN & CARD ACTIONS ---

def toggle_dropdown(p_id):
    """Toggle the visibility of a project card dropdown."""
    # First hide all active dropdowns to prevent multiple active ones
    dropdowns = document.querySelectorAll('.dropdown-menu')
    for d in dropdowns:
        if d.id != f"dropdown-{p_id}":
            d.style.display = "none"
            
    dd = document.getElementById(f"dropdown-{p_id}")
    if dd:
        if dd.style.display == "none":
            dd.style.display = "block"
        else:
            dd.style.display = "none"

# Global JS bridges for the inline onclick handlers in the HTML
window.toggleDropdown = create_proxy(toggle_dropdown)

def toggle_pin(p_id):
    for p in app_state["projects"]:
        if p.get("id") == p_id:
            p["is_pinned"] = not p.get("is_pinned", False)
            p["updated_at"] = datetime.now().isoformat()
            break
    save_data()
    render_projects()

window.togglePin = create_proxy(toggle_pin)

def delete_project(p_id):
    should_delete = window.confirm("Are you sure you want to delete this project? This action cannot be undone.")
    if should_delete:
        app_state["projects"] = [p for p in app_state["projects"] if p.get("id") != p_id]
        save_data()
        render_projects()

window.deleteProject = create_proxy(delete_project)

def open_edit_modal(p_id):
    # Hide dropdown
    toggle_dropdown(p_id)
    
    project = None
    for p in app_state["projects"]:
        if p.get("id") == p_id:
            project = p
            break
            
    if not project: return
    
    modal = document.getElementById("edit-modal")
    if modal:
        modal.style.display = "flex"
        document.getElementById("edit-project-id").value = p_id
        document.getElementById("edit-project-name").value = project.get("name", "")
        document.getElementById("edit-project-desc").value = project.get("description", "")
        
        cat = project.get("category", "none")
        radios = document.querySelectorAll('input[name="edit-project-category"]')
        for r in radios:
            r.checked = (r.value == cat)

window.openEditModal = create_proxy(open_edit_modal)

def close_edit_modal(e):
    modal = document.getElementById("edit-modal")
    if modal:
        modal.style.display = "none"

def save_edit_project(e):
    p_id = document.getElementById("edit-project-id").value
    name_input = document.getElementById("edit-project-name")
    desc_input = document.getElementById("edit-project-desc")
    
    name_val = name_input.value.strip()
    if not name_val:
        name_input.style.border = "1px solid red"
        return
        
    name_input.style.border = ""
    desc_val = desc_input.value.strip()
    
    category = "none"
    radios = document.querySelectorAll('input[name="edit-project-category"]')
    for r in radios:
        if r.checked:
            category = r.value
            break
            
    for p in app_state["projects"]:
        if p.get("id") == p_id:
            p["name"] = name_val
            p["description"] = desc_val
            p["category"] = category
            p["updated_at"] = datetime.now().isoformat()
            break
            
    save_data()
    close_edit_modal(None)
    render_projects()


# --- PROJECT DETAILS VIEW & TASKS ---

SORT_PRIORITY = {"high": 3, "medium": 2, "low": 1}

def open_project(p_id):
    app_state["active_project_id"] = p_id
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    
    document.getElementById("app").style.display = "none"
    document.getElementById("project-view").style.display = "flex"
    document.getElementById("current-project-title").innerText = project.get("name", "Project")
    
    # Hide any open dropdowns
    dropdowns = document.querySelectorAll('.dropdown-menu')
    for d in dropdowns: d.style.display = "none"
        
    render_tasks()

window.openProject = create_proxy(open_project)

def back_to_projects(e):
    app_state["active_project_id"] = None
    document.getElementById("project-view").style.display = "none"
    document.getElementById("app").style.display = "flex"
    render_projects() # Update project metadata like time

def render_tasks():
    p_id = app_state["active_project_id"]
    if not p_id: return
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    
    tasks = project.get("tasks", [])
    
    # Sorting
    sort_type = app_state.get("task_sort", "last_added")
    if sort_type == "last_added":
        tasks = sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)
    elif sort_type == "first_added":
        tasks = sorted(tasks, key=lambda x: x.get("created_at", ""))
    elif sort_type == "priority":
        tasks = sorted(tasks, key=lambda x: SORT_PRIORITY.get(x.get("priority", "medium"), 0), reverse=True)

    completed_tasks = [t for t in tasks if t.get("completed")]
    active_tasks = [t for t in tasks if not t.get("completed")]
    
    total = len(tasks)
    completed_count = len(completed_tasks)
    percent = int((completed_count / total * 100)) if total > 0 else 0
    
    p_element = document.getElementById("milestone-percent")
    if p_element: p_element.innerText = f"{percent}%"
    f_element = document.getElementById("milestone-fill")
    if f_element: f_element.style.width = f"{percent}%"
    
    act_container = document.getElementById("active-tasks-list")
    comp_container = document.getElementById("completed-tasks-list")
    
    if act_container:
        act_container.innerHTML = ""
        if not active_tasks:
            act_container.innerHTML = "<p style='color: var(--text-secondary); font-size: 0.9rem; padding: 1rem; border: 1px dashed var(--border-color); border-radius: 12px; text-align: center;'>No active tasks.</p>"
        else:
            for t in active_tasks:
                act_container.appendChild(create_task_element(t, project))
                
    if comp_container:
        comp_container.innerHTML = ""
        if not completed_tasks:
             comp_container.innerHTML = "<p style='color: var(--text-secondary); font-size: 0.9rem; padding: 1rem; border: 1px dashed var(--border-color); border-radius: 12px; text-align: center;'>No completed tasks.</p>"
        else:
            for t in completed_tasks:
                comp_container.appendChild(create_task_element(t, project))

def create_task_element(task, project):
    t_id = task.get("id")
    is_completed = task.get("completed", False)
    
    priority = task.get("priority", "medium")
    pri_class = f"priority-{priority}"
    pri_icon = "drag_handle"
    pri_text = "Medium Priority"
    if priority == "high":
        pri_icon = "keyboard_double_arrow_up"
        pri_text = "High Priority"
    elif priority == "low":
        pri_icon = "keyboard_double_arrow_down"
        pri_text = "Low Priority"
        
    tag_id = task.get("tag_id")
    tag_html = ""
    if tag_id:
        custom_tags = project.get("custom_tags", [])
        tag = next((tg for tg in custom_tags if tg.get("id") == tag_id), None)
        if tag:
            bg_color = tag.get("color", "var(--primary-color)")
            tag_html = f'<span class="task-tag" style="background-color: {bg_color}33; color: {bg_color}; border: 1px solid {bg_color}66;">{tag.get("name", "")}</span>'
            
    comp_class = "completed" if is_completed else ""
    item_class = "is-completed" if is_completed else ""
    
    el = document.createElement("div")
    el.className = f"task-item {item_class}"
    
    el.innerHTML = f"""
        <div class="task-checkbox {comp_class}" onclick="event.stopPropagation(); toggleTaskCompletion('{project.get('id')}', '{t_id}')">
            <span class="material-icons-round">check</span>
        </div>
        <div class="task-content">
            <div class="task-title">{task.get("title", "")}</div>
            <div class="task-meta">
                <span class="task-meta-item {pri_class}">
                    <span class="material-icons-round" style="font-size: 1rem;">{pri_icon}</span> {pri_text}
                </span>
                {tag_html}
            </div>
        </div>
        <button class="icon-btn btn-small" style="color: #EF4444; opacity: 0.5; margin-top: -0.2rem;" onclick="event.stopPropagation(); deleteTask('{project.get('id')}', '{t_id}')">
            <span class="material-icons-round">delete_outline</span>
        </button>
    """
    return el

def toggle_task(p_id, t_id):
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    tasks = project.get("tasks", [])
    for t in tasks:
        if t.get("id") == t_id:
            t["completed"] = not t.get("completed", False)
            break
    project["updated_at"] = datetime.now().isoformat()
    save_data()
    render_tasks()

window.toggleTaskCompletion = create_proxy(toggle_task)

def delete_task(p_id, t_id):
    should_del = window.confirm("Delete this task?")
    if not should_del: return
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    project["tasks"] = [t for t in project.get("tasks", []) if t.get("id") != t_id]
    project["updated_at"] = datetime.now().isoformat()
    save_data()
    render_tasks()

window.deleteTask = create_proxy(delete_task)

def task_sort_change(e):
    app_state["task_sort"] = e.target.value
    render_tasks()

# --- Modals for Tasks and Tags ---

def open_task_modal(e):
    p_id = app_state["active_project_id"]
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    
    tag_container = document.getElementById("task-tag-container")
    # Clean previous tags except the NEW button
    for child in list(tag_container.children):
        if child.id != "btn-new-tag-modal":
            child.remove()
            
    # Add "No Tag" option
    no_tag_html = f'''
        <label class="tag-option-label" style="--tag-color: var(--text-secondary);">
            <input type="radio" name="task-custom-tag" value="none" checked>
            <span class="tag-option-btn">No Tag</span>
        </label>
    '''
    container_temp = document.createElement("div")
    container_temp.innerHTML = no_tag_html
    tag_container.insertBefore(container_temp.firstElementChild, document.getElementById("btn-new-tag-modal"))
    
    for tg in project.get("custom_tags", []):
        tg_id = tg.get("id", "")
        tg_name = tg.get("name", "")
        tg_color = tg.get("color", "var(--primary-color)")
        html = f'''
            <label class="tag-option-label" style="--tag-color: {tg_color};">
                <input type="radio" name="task-custom-tag" value="{tg_id}">
                <span class="tag-option-btn">{tg_name}</span>
            </label>
        '''
        temp = document.createElement("div")
        temp.innerHTML = html
        tag_container.insertBefore(temp.firstElementChild, document.getElementById("btn-new-tag-modal"))
        
    document.getElementById("task-title").value = ""
    radios = document.querySelectorAll('input[name="task-priority"]')
    for r in radios:
        if r.value == "medium": r.checked = True
    
    document.getElementById("create-task-modal").style.display = "flex"
    
def close_task_modal(e):
    document.getElementById("create-task-modal").style.display = "none"

def save_new_task(e):
    p_id = app_state["active_project_id"]
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    
    title_el = document.getElementById("task-title")
    title = title_el.value.strip()
    if not title:
        title_el.style.border = "1px solid red"
        return
    title_el.style.border = ""
    
    priority_radios = document.querySelectorAll('input[name="task-priority"]')
    priority = "medium"
    for r in priority_radios:
        if r.checked:
            priority = r.value
            break
            
    tag_radios = document.querySelectorAll('input[name="task-custom-tag"]')
    tag_id = "none"
    for r in tag_radios:
        if r.checked:
            tag_id = r.value
            break
            
    if tag_id == "none":
        tag_id = ""
    
    if "tasks" not in project: project["tasks"] = []
    
    import time
    t_id = f"task_{int(time.time() * 1000)}"
    new_task = {
        "id": t_id,
        "title": title,
        "priority": priority,
        "tag_id": tag_id,
        "completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    project["tasks"].insert(0, new_task)
    project["updated_at"] = datetime.now().isoformat()
    save_data()
    
    close_task_modal(None)
    render_tasks()

def open_tag_modal(e):
    document.getElementById("new-tag-name").value = ""
    document.getElementById("create-tag-modal").style.display = "flex"

def close_tag_modal(e):
    document.getElementById("create-tag-modal").style.display = "none"

def save_new_tag(e):
    p_id = app_state["active_project_id"]
    project = next((p for p in app_state["projects"] if p.get("id") == p_id), None)
    if not project: return
    
    name_el = document.getElementById("new-tag-name")
    name = name_el.value.strip()
    if not name:
        name_el.style.border = "1px solid red"
        return
    name_el.style.border = ""
        
    color = document.getElementById("new-tag-color").value
    
    if "custom_tags" not in project: project["custom_tags"] = []
    
    import time
    tg_id = f"tag_{int(time.time() * 1000)}"
    new_tag = {"id": tg_id, "name": name, "color": color}
    project["custom_tags"].append(new_tag)
    save_data()
    
    close_tag_modal(None)
    
    tag_container = document.getElementById("task-tag-container")
    html = f'''
        <label class="tag-option-label" style="--tag-color: {color};">
            <input type="radio" name="task-custom-tag" value="{tg_id}" checked>
            <span class="tag-option-btn">{name}</span>
        </label>
    '''
    temp = document.createElement("div")
    temp.innerHTML = html
    tag_container.insertBefore(temp.firstElementChild, document.getElementById("btn-new-tag-modal"))


# --- THEME AND SPLASH (Kept from previous) ---

def hide_splash():
    splash = document.getElementById("splash-screen")
    app = document.getElementById("app")
    if splash:
        splash.style.display = "none"
    if app:
        app.style.display = "flex"

def toggle_theme(e):
    html = document.documentElement
    current_theme = html.getAttribute("data-theme")
    icon = document.getElementById("theme-icon")
    
    if current_theme == "dark":
        html.removeAttribute("data-theme")
        if icon: icon.innerText = "dark_mode"
        window.localStorage.setItem('fernle-theme', 'light')
    else:
        html.setAttribute("data-theme", "dark")
        if icon: icon.innerText = "light_mode"
        window.localStorage.setItem('fernle-theme', 'dark')

def set_initial_theme_icon():
    html = document.documentElement
    current_theme = html.getAttribute("data-theme")
    icon = document.getElementById("theme-icon")
    if icon:
        if current_theme == "dark": icon.innerText = "light_mode"
        else: icon.innerText = "dark_mode"

# --- INITIALIZATION ---

def init():
    # 1. Theme Setup
    theme_btn = document.getElementById("theme-toggle")
    if theme_btn:
        theme_btn.addEventListener("click", create_proxy(toggle_theme))
    set_initial_theme_icon()
    
    # 2. Data loading
    load_data()
    
    # 3. Setup UI bindings
    # Tabs
    tabs = document.querySelectorAll('.tab')
    for tab in tabs:
        tab.addEventListener("click", create_proxy(handle_tab_click))
        
    # Modal logic (Create)
    fab = document.getElementById("fab-add")
    if fab: fab.addEventListener("click", create_proxy(open_create_modal))
    
    close_btn1 = document.getElementById("close-modal-cancel")
    if close_btn1: close_btn1.addEventListener("click", create_proxy(close_create_modal))
    
    close_btn2 = document.getElementById("btn-cancel-project")
    if close_btn2: close_btn2.addEventListener("click", create_proxy(close_create_modal))
    
    save_btn = document.getElementById("btn-save-project")
    if save_btn: save_btn.addEventListener("click", create_proxy(save_new_project))
    
    # Modal logic (Edit)
    edit_close_btn1 = document.getElementById("close-modal-edit")
    if edit_close_btn1: edit_close_btn1.addEventListener("click", create_proxy(close_edit_modal))
    
    edit_close_btn2 = document.getElementById("btn-cancel-edit-project")
    if edit_close_btn2: edit_close_btn2.addEventListener("click", create_proxy(close_edit_modal))
    
    edit_save_btn = document.getElementById("btn-update-project")
    if edit_save_btn: edit_save_btn.addEventListener("click", create_proxy(save_edit_project))
    
    # Global click handler for closing dropdowns when clicking outside
    def window_click_handler(e):
        # Because we added event.stopPropagation() on the buttons,
        # anything reaching here means it's an outside click.
        dropdowns = document.querySelectorAll('.dropdown-menu')
        for d in dropdowns:
            d.style.display = "none"

    window.addEventListener("click", create_proxy(window_click_handler))
    
    # Project View Logic
    btn_back = document.getElementById("btn-back-projects")
    if btn_back: btn_back.addEventListener("click", create_proxy(back_to_projects))
    
    sort_select = document.getElementById("task-sort-select")
    if sort_select: sort_select.addEventListener("change", create_proxy(task_sort_change))
    
    btn_add_task = document.getElementById("btn-open-add-task")
    if btn_add_task: btn_add_task.addEventListener("click", create_proxy(open_task_modal))
    
    # Task Modal Setup
    tm_close = document.getElementById("close-modal-task")
    if tm_close: tm_close.addEventListener("click", create_proxy(close_task_modal))
    tm_can = document.getElementById("btn-cancel-task")
    if tm_can: tm_can.addEventListener("click", create_proxy(close_task_modal))
    tm_save = document.getElementById("btn-save-task")
    if tm_save: tm_save.addEventListener("click", create_proxy(save_new_task))
    
    # Tag Modal Setup
    btn_new_tag = document.getElementById("btn-new-tag-modal")
    if btn_new_tag: btn_new_tag.addEventListener("click", create_proxy(open_tag_modal))
    
    tg_close = document.getElementById("close-modal-tag")
    if tg_close: tg_close.addEventListener("click", create_proxy(close_tag_modal))
    tg_can = document.getElementById("btn-cancel-tag")
    if tg_can: tg_can.addEventListener("click", create_proxy(close_tag_modal))
    tg_save = document.getElementById("btn-save-tag-action")
    if tg_save: tg_save.addEventListener("click", create_proxy(save_new_tag))

    # 4. Initial Render
    render_projects()
    
    # 5. Hide splash screen
    hide_splash()

init()
