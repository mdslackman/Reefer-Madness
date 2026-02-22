import tkinter as tk
from tkinter import ttk, messagebox
import csv, os, sqlite3
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re

class ReeferMadness:
    # Constants for unit conversions
    DKH_TO_PPM_FACTOR = 17.86  # dKH to ppm conversion factor
    LITERS_PER_GALLON = 3.785
    
    def __init__(self, root):
        self.root = root
        self.root.title("Reefer Madness v0.25.0 - Interactive Pro (Improved)")
        self.root.geometry("720x600")  # Reduced from 900 to 720 (1/5th smaller)
        self.root.minsize(600, 500)   # Adjusted minimum size proportionally
        
        # Parameter database - renamed from 'db' for clarity
        self.param_config = {
            "Alkalinity": {
                "target": 8.5, "low": 7.5, "high": 9.5, "max_daily": 1.4, "unit": "dKH", "custom_unit": "dKH per mL",
                "dosing": {
                    # Two-Part Systems (Most Popular)
                    "Fritz RPM Liquid": 1.4,  # 1.4 dKH per mL
                    "ESV B-Ionic Pt 1": 1.4,  # 1.4 dKH per mL  
                    "BRS 2-Part": 1.4,  # 1.4 dKH per mL
                    "Aquaforest Component 1+": 1.0,  # 1.0 dKH per mL
                    
                    # Single Solutions  
                    "Red Sea Foundation B (KH/Alkalinity)": 0.36,  # 0.36 dKH per mL
                    "Seachem Reef Builder": 0.6,  # 0.6 dKH per mL
                    "Brightwell Alkalin8.3": 0.5,  # 0.5 dKH per mL
                    "Tropic Marin Bio-Calcium": 0.8,  # 0.8 dKH per mL
                    "Fauna Marin Balling Method Part A": 1.2,  # 1.2 dKH per mL
                    
                    # All-in-One Systems
                    "Red Sea Reef Foundation ABC+": 0.4,  # 0.4 dKH per mL
                    "Triton Core7 Base Elements 1": 0.9,  # 0.9 dKH per mL
                    "Aquaforest Reef Mineral Salt": 0.7,  # 0.7 dKH per mL
                    
                    "Custom": 1.0
                },
                "kits": {
                    "Hanna HI772 dKH Checker": [
                        "1. Clean cuvette with lint-free cloth - wipe thoroughly",
                        "2. Fill cuvette to 10ml line with tank water using syringe", 
                        "3. Secure cap and wipe cuvette exterior clean",
                        "4. Press button to power on - wait for 'C1' on display",
                        "5. Insert water cuvette and press button to zero",
                        "6. Wait for 'C2' display, then remove cuvette",
                        "7. Draw exactly 1ml reagent into small syringe",
                        "8. Add reagent to cuvette and shake vigorously for 2 mins",
                        "9. Wipe cuvette clean and insert when ready",
                        "10. Press button and read dKH result on display"
                    ],
                    "Salifert KH/Alkalinity Kit": [
                        "1. Use 5ml syringe to add exactly 4ml tank water to test vial",
                        "2. Shake KH-Ind indicator bottle several times",
                        "3. Add exactly 2 drops KH-Ind to vial (liquid will turn blue)",
                        "4. Attach plastic tip firmly to 1ml titration syringe", 
                        "5. Draw KH reagent to exactly 1.00ml mark (ignore air bubbles)",
                        "6. Add reagent drop-by-drop while swirling after each drop",
                        "7. Continue until color changes from blue/green to orange-red or pink",
                        "8. Hold syringe tip up and read scale at upper edge of black piston",
                        "9. Find dKH value on included conversion table",
                        "10. Calculate: dKH = (1 - syringe reading) × 16"
                    ],
                    "Red Sea Reef Foundation Test Kit": [
                        "1. Fill syringe with exactly 5ml tank water into test vial",
                        "2. Add 5 drops Foundation B testing solution",
                        "3. Add 1 level scoop of powder reagent using included spoon",
                        "4. Cap vial and shake vigorously until powder dissolves",
                        "5. Solution should turn blue - continue shaking if needed",
                        "6. Fill 1ml syringe with titrant to exactly 1.00ml mark",
                        "7. Add titrant drop-by-drop while swirling gently",
                        "8. Stop when color changes from blue to pink/red",
                        "9. Read remaining volume in syringe",
                        "10. Calculate: dKH = (1.00 - reading) × 20"
                    ],
                    "API KH Test Kit": [
                        "1. Fill test tube to 5ml line with tank water",
                        "2. Add 1 drop test solution and swirl gently",
                        "3. Continue adding drops one at a time",
                        "4. Swirl after each drop addition",
                        "5. Count each drop carefully",
                        "6. Stop when color changes from blue to yellow-green",
                        "7. Count the total number of drops used",
                        "8. Each drop = 1 degree of carbonate hardness",
                        "9. For dKH: multiply drops by 0.178",
                        "10. Target range: 7-12 dKH for reef tanks"
                    ]
                }
            },
            "Calcium": {
                "target": 420, "low": 400, "high": 440, "max_daily": 25.0, "unit": "ppm", "custom_unit": "PPM per mL",
                "dosing": {
                    # Two-Part Systems
                    "Fritz RPM Liquid": 20,  # 20 ppm per mL
                    "ESV B-Ionic Pt 2": 20,  # 20 ppm per mL
                    "BRS 2-Part": 20,  # 20 ppm per mL
                    "Aquaforest Component 2+": 15,  # 15 ppm per mL
                    
                    # Single Solutions
                    "Red Sea Foundation C (Ca/Calcium)": 5.5,  # 5.5 ppm per mL
                    "Seachem Reef Complete": 10,  # 10 ppm per mL
                    "Brightwell Calcion": 12,  # 12 ppm per mL
                    "Tropic Marin Bio-Calcium": 18,  # 18 ppm per mL
                    "Fauna Marin Balling Method Part B": 25,  # 25 ppm per mL
                    
                    # Reactor Media (liquid equivalent)
                    "CaribSea ARM Media": 8,  # 8 ppm per mL equivalent
                    "Bulk Reef Supply Calcium Hydroxide": 30,  # 30 ppm per mL (kalk)
                    
                    # All-in-One
                    "Red Sea Reef Foundation ABC+": 6,  # 6 ppm per mL  
                    "Triton Core7 Base Elements 2": 22,  # 22 ppm per mL
                    
                    "Custom": 15.0
                },
                "kits": {
                    "Red Sea Pro Calcium Kit": [
                        "1. Use 5ml syringe to add exactly 5ml tank water to test vial",
                        "2. Add exactly 5 drops Ca-A indicator reagent",
                        "3. Add 1 level scoop Ca-B powder using provided spoon",
                        "4. Cap vial and shake vigorously until powder dissolves", 
                        "5. Solution should turn pink/red color",
                        "6. Fill titration syringe with Ca-C reagent to 0ml mark",
                        "7. Add reagent drop-by-drop while swirling between drops",
                        "8. Continue until color changes from pink to blue",
                        "9. Read calcium value directly from syringe scale",
                        "10. Result is displayed in ppm (mg/L) calcium"
                    ],
                    "Salifert Calcium Kit": [
                        "1. Add exactly 2ml tank water to test vial using syringe",
                        "2. Add 8 drops Ca-1 indicator reagent",
                        "3. Add 1 level scoop Ca-2 powder and shake to dissolve",
                        "4. Solution turns pink - swirl for 10 seconds",
                        "5. Fill 1ml syringe with Ca-3 titrant to 1.00ml mark",
                        "6. Add titrant drop-by-drop while swirling gently",
                        "7. Continue until color changes from pink to blue",
                        "8. Read remaining volume in syringe",
                        "9. Calculate: Ca ppm = (1.00 - reading) × 400",
                        "10. For 1ml sample: multiply result by 2"
                    ]
                }
            },
            "Magnesium": {
                "target": 1350, "low": 1280, "high": 1420, "max_daily": 100.0, "unit": "ppm", "custom_unit": "PPM per mL",
                "dosing": {
                    # Two-Part Systems  
                    "Fritz RPM Liquid": 100,  # 100 ppm per mL
                    "ESV B-Ionic Magnesium": 30,  # 30 ppm per mL
                    "BRS Magnesium": 75,  # 75 ppm per mL
                    "Aquaforest Component Mg": 50,  # 50 ppm per mL
                    
                    # Single Solutions
                    "Red Sea Foundation A (Mg/Magnesium)": 15,  # 15 ppm per mL
                    "Seachem Reef Magnesium": 25,  # 25 ppm per mL
                    "Brightwell MagnesIon": 40,  # 40 ppm per mL
                    "Tropic Marin Bio-Magnesium": 60,  # 60 ppm per mL
                    "Fauna Marin Balling Method Part C": 80,  # 80 ppm per mL
                    
                    # All-in-One
                    "Triton Core7 Base Elements 3": 45,  # 45 ppm per mL
                    "Kent Marine Liquid Magnesium": 20,  # 20 ppm per mL
                    
                    "Custom": 50.0
                },
                "kits": {
                    "Salifert Magnesium Kit": [
                        "1. Add exactly 2ml tank water to test vial",
                        "2. Add exactly 6 drops Mg-1 reagent (turns blue)",
                        "3. Swirl gently to mix - solution remains blue",
                        "4. Fill 1ml syringe with Mg-2 titrant to 1.00ml mark",
                        "5. Add titrant very slowly while swirling constantly",
                        "6. Continue until color changes from blue to pink/red",
                        "7. Read remaining volume in syringe carefully",
                        "8. Calculate: Mg ppm = (1.00 - reading) × 1500",
                        "9. Natural seawater = ~1300-1350 ppm",
                        "10. Maintain between 1280-1420 ppm for reef tanks"
                    ],
                    "Red Sea Magnesium Kit": [
                        "1. Fill test vial with exactly 10ml tank water",
                        "2. Add 10 drops Mg-A reagent and swirl",
                        "3. Add 3 drops Mg-B reagent (solution turns blue)",
                        "4. Fill syringe with Mg-C titrant to 0ml mark",
                        "5. Add titrant drop-by-drop while swirling",
                        "6. Color will change through purple to pink",
                        "7. Stop when color is clear pink (no blue tint)",
                        "8. Read magnesium value directly from syringe",
                        "9. Each 0.1ml = ~120 ppm magnesium",
                        "10. Ideal range: 1300-1400 ppm"
                    ]
                }
            },
            "Nitrate": { 
                "target": 5.0, "low": 2.0, "high": 10.0, "max_daily": 5.0, "unit": "ppm", "custom_unit": "PPM per mL", 
                "dosing": {"Custom": 1.0}, 
                "kits": {
                    "Salifert Nitrate Kit": [
                        "1. Add exactly 1ml tank water to test vial",
                        "2. Add 6 drops NO3-1 reagent and swirl gently",
                        "3. Add 1 level scoop NO3-2 powder using spoon",
                        "4. Cap and shake vigorously for 10 seconds",
                        "5. Wait exactly 3 mins for color development (set timer)",
                        "6. Compare color to provided color chart",
                        "7. Match closest color under good lighting",
                        "8. Read nitrate value from chart (ppm)",
                        "9. For reef tanks: maintain 2-10 ppm",
                        "10. Higher readings may indicate feeding/filtration issues"
                    ],
                    "API Nitrate Test Kit": [
                        "1. Fill test tube to 5ml line with tank water",
                        "2. Add 10 drops Solution #1 and shake",
                        "3. Add 10 drops Solution #2 and shake vigorously",
                        "4. Wait exactly 5 mins for color development",
                        "5. Shake again after waiting period",
                        "6. Compare to color chart under white light",
                        "7. Hold tube against white background",
                        "8. Match color from top down through solution",
                        "9. Read ppm value from chart",
                        "10. Reef target: 2-10 ppm nitrate"
                    ]
                }
            },
            "Phosphate": { 
                "target": 0.03, "low": 0.01, "high": 0.08, "max_daily": 0.02, "unit": "ppm", "custom_unit": "PPM per mL", 
                "dosing": {"Custom": 1.0}, 
                "kits": {
                    "Hanna HI713 Low Range": [
                        "1. Clean both cuvettes thoroughly with lint-free cloth",
                        "2. Fill one cuvette to 10ml with tank water (sample)",
                        "3. Fill second cuvette to 10ml with tank water (blank)",
                        "4. Cap both cuvettes and wipe exteriors clean",
                        "5. Power on checker - wait for 'C1' display",
                        "6. Insert blank cuvette and press button to zero",
                        "7. Wait for 'C2', remove blank cuvette",
                        "8. Open sample cuvette and add 1 packet HI713-25 reagent",
                        "9. Cap and shake vigorously for 10 seconds", 
                        "10. Wait exactly 3 mins, then insert and read result"
                    ],
                    "Hanna HI736 Ultra Low Range": [
                        "1. Mark cuvette and checker for consistent alignment",
                        "2. Clean cuvettes with lint-free cloth until spotless",
                        "3. Fill both cuvettes to 10ml line with tank water",
                        "4. Cap both and wipe completely clean",
                        "5. Power on - insert blank aligned with marks at 'C1'",
                        "6. Press button to zero, wait for 'C2'",
                        "7. Remove blank, add reagent packet to sample",
                        "8. Cap sample and shake vigorously for 15 seconds",
                        "9. Wait exactly 3 mins for color development",
                        "10. Insert sample aligned with marks and read result"
                    ],
                    "Salifert Phosphate Kit": [
                        "1. Add exactly 4ml tank water to test vial",
                        "2. Add 2.5ml PO4-1 reagent using large syringe",
                        "3. Add exactly 6 drops PO4-2 reagent",
                        "4. Swirl gently to mix all reagents",
                        "5. Wait exactly 3 mins for color development",
                        "6. Compare color to chart under white light",
                        "7. Look through vial from top down",
                        "8. Match closest color on provided chart",
                        "9. Read phosphate value (typical: 0.01-0.10 ppm)",
                        "10. Lower is better for reef tanks (target <0.05 ppm)"
                    ]
                }
            }
        }

        # File paths
        self.log_file = os.path.join(os.path.expanduser("~/Documents/ReeferMadness"), "reef_pro_v25.csv")
        if not os.path.exists(os.path.dirname(self.log_file)): 
            os.makedirs(os.path.dirname(self.log_file))
        
        # SQLite database path
        self.db_path = os.path.join(os.path.expanduser("~/Documents/ReeferMadness"), "reef_pro_v25.db")
        self.init_database()

        # Variables with better initialization - start with 0 tank volume
        self.tank_volume = tk.StringVar(value=self.load_tank_volume())  # Load saved volume or default to 0
        self.volume_unit = tk.StringVar(value="Gallons")
        self.selected_parameter = tk.StringVar(value="Alkalinity")
        self.selected_brand = tk.StringVar()
        self.current_value = tk.StringVar()
        self.target_value = tk.StringVar(value="8.5")
        self.ph_value = tk.StringVar()
        self.alkalinity_unit = tk.StringVar(value="dKH")
        self.custom_strength = tk.StringVar(value="1.4")
        
        # Consumption Tracker Variables
        self.cons_parameter = tk.StringVar(value="Alkalinity")
        self.cons_brand = tk.StringVar()
        self.cons_start = tk.StringVar()
        self.cons_end = tk.StringVar()
        self.cons_days = tk.StringVar(value="0")  # Default to 0 instead of 3
        self.cons_alk_unit = tk.StringVar(value="dKH")
        self.maint_custom_strength = tk.StringVar(value="1.0")

        # Add trace to save tank volume when changed
        self.tank_volume.trace_add("write", self.save_tank_volume)

        # Create notebook and scrollable tabs
        self.notebook = ttk.Notebook(self.root)
        
        # Create scrollable frames for each tab
        self.tabs = {}
        self.tab_canvases = {}
        self.tab_scrollbars = {}
        self.tab_frames = {}
        
        for name in ["Action Plan", "Maintenance", "Trends", "History"]:
            # Create the main tab frame
            main_frame = ttk.Frame(self.notebook)
            
            # Create canvas and thicker scrollbar for this tab
            canvas = tk.Canvas(main_frame)
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview, width=20)  # Thicker scrollbar
            scrollable_frame = ttk.Frame(canvas)
            
            # Configure scrolling
            scrollable_frame.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Enhanced mouse wheel scrolling - bind to canvas and main frame
            def _on_mouse_wheel(event, c=canvas):
                c.yview_scroll(int(-1*(event.delta/120)), "units")
                
            def _on_enter(event, c=canvas):
                c.focus_set()  # Give canvas focus when mouse enters
            
            # Bind mouse wheel events to multiple widgets for better coverage
            canvas.bind("<MouseWheel>", _on_mouse_wheel)  # Windows
            canvas.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1, "units"))  # Linux
            canvas.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1, "units"))   # Linux
            canvas.bind("<Enter>", _on_enter)  # Focus when mouse enters
            
            main_frame.bind("<MouseWheel>", _on_mouse_wheel)  # Windows
            main_frame.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1, "units"))  # Linux  
            main_frame.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1, "units"))   # Linux
            
            scrollable_frame.bind("<MouseWheel>", _on_mouse_wheel)  # Windows
            scrollable_frame.bind("<Button-4>", lambda e, c=canvas: c.yview_scroll(-1, "units"))  # Linux
            scrollable_frame.bind("<Button-5>", lambda e, c=canvas: c.yview_scroll(1, "units"))   # Linux
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Store references
            self.tabs[name] = scrollable_frame  # This is what build functions will use
            self.tab_canvases[name] = canvas
            self.tab_scrollbars[name] = scrollbar
            self.tab_frames[name] = main_frame
            
            # Add to notebook
            self.notebook.add(main_frame, text=f" {name} ")
        
        self.notebook.pack(expand=True, fill="both")

        # Build all tabs
        self.build_action_plan()
        self.build_maintenance()
        self.build_trends()
        self.build_history()
        
        # Set up event traces
        self.setup_event_traces()
        
        # Timer state
        self.timer_running = False
        self.timer_after_id = None
        
        # Clear daily log values on startup (session-only data)
        self.clear_daily_log_on_startup()
        
        # Initialize UI
        self.sync_action_ui()
        self.sync_maintenance_ui()  # Add this missing call

    def load_tank_volume(self):
        """Load saved tank volume from preferences file, default to 0"""
        prefs_file = os.path.join(os.path.expanduser("~/Documents/ReeferMadness"), "preferences.txt")
        try:
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r') as f:
                    content = f.read().strip()
                    if content and float(content) > 0:
                        return content
        except (ValueError, IOError):
            pass
        return "0"  # Default to 0 instead of 220

    def save_tank_volume(self, *args):
        """Save tank volume to preferences file whenever it changes"""
        try:
            volume_str = self.tank_volume.get().strip()
            if volume_str and float(volume_str) >= 0:  # Only save valid positive numbers
                prefs_file = os.path.join(os.path.expanduser("~/Documents/ReeferMadness"), "preferences.txt")
                with open(prefs_file, 'w') as f:
                    f.write(volume_str)
        except (ValueError, IOError):
            pass  # Ignore errors during saving

    def clear_daily_log_on_startup(self):
        """Clear daily log input fields on app startup (session-only data)"""
        # Clear all daily log input fields - these should not persist across sessions
        for param in self.log_variables:
            self.log_variables[param].set("")
        
        # Reset alkalinity unit to default
        self.log_alk_unit.set("dKH")
        
        # Optional: Clear test database if needed (uncomment for clean testing)
        # self.clear_test_database()
        
        print("✅ Session data cleared for fresh start")
        
    def clear_test_database(self):
        """Clear all test data for fresh start - useful for testing"""
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM logs')
                conn.commit()
                conn.close()
                print("✅ Test database cleared")
                return True
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            return False
        
        # Note: Tank volume IS NOT cleared - it persists across sessions
        # Note: Action Plan and Consumption values are also cleared automatically since they use StringVar() without persistence

    def setup_event_traces(self):
        """Set up all variable traces for UI synchronization"""
        self.selected_parameter.trace_add("write", self.sync_action_ui)
        self.selected_brand.trace_add("write", self.toggle_custom_visibility)
        self.current_value.trace_add("write", self.auto_unit_detection)
        # Removed auto-population traces - keeping Daily Log simple
        self.alkalinity_unit.trace_add("write", self.update_target_by_unit)
        
        self.cons_parameter.trace_add("write", self.sync_maintenance_ui)
        self.cons_brand.trace_add("write", self.toggle_maint_custom_visibility)
        
        # Add auto-detection for consumption calculator alkalinity values
        self.cons_start.trace_add("write", self.auto_cons_start_unit_detection)
        self.cons_end.trace_add("write", self.auto_cons_end_unit_detection)
        # Removed auto-population from consumption - keeping it simple

    def validate_numeric_input(self, value, min_val=None, max_val=None, allow_negative=False):
        """Validate numeric input with optional range checking"""
        if not value:
            return True, ""
            
        try:
            num_val = float(value)
            if not allow_negative and num_val < 0:
                return False, "Value cannot be negative"
            if min_val is not None and num_val < min_val:
                return False, f"Value must be at least {min_val}"
            if max_val is not None and num_val > max_val:
                return False, f"Value cannot exceed {max_val}"
            return True, ""
        except ValueError:
            return False, "Please enter a valid number"

    def auto_unit_detection(self, *args):
        """Automatically detect alkalinity units based on entered value"""
        if self.selected_parameter.get() == "Alkalinity":
            try:
                val_str = self.current_value.get().strip()
                if val_str:
                    val = float(val_str)
                    # Values > 50 are almost certainly ppm (typical range 120-180)
                    # Values <= 20 are almost certainly dKH (typical range 7-12)
                    if val > 50 and self.alkalinity_unit.get() == "dKH":
                        self.alkalinity_unit.set("ppm")
                    elif val <= 20 and self.alkalinity_unit.get() == "ppm":
                        self.alkalinity_unit.set("dKH")
            except ValueError:
                pass

    def auto_log_unit_detection(self, *args):
        """Automatically detect alkalinity units for daily logging based on entered value"""
        try:
            val_str = self.log_variables["Alkalinity"].get().strip()
            if val_str:
                val = float(val_str)
                # Same improved logic
                if val > 50 and self.log_alk_unit.get() == "dKH":
                    self.log_alk_unit.set("ppm")
                elif val <= 20 and self.log_alk_unit.get() == "ppm":
                    self.log_alk_unit.set("dKH")
        except ValueError:
            pass

    def populate_daily_log_from_current(self, *args):
        """Auto-populate daily log when user enters current value in Action Plan"""
        try:
            current_val = self.current_value.get().strip()
            selected_param = self.selected_parameter.get()
            
            if current_val and selected_param in self.log_variables:
                # Parse the value to make sure it's valid
                test_val = float(current_val)  # Validate it's a number
                
                # Only populate if the log field is currently empty (don't overwrite user data)
                current_log_val = self.log_variables[selected_param].get().strip()
                if not current_log_val:
                    # Set the full value, not just validation result
                    self.log_variables[selected_param].set(current_val)
                    
                    # For alkalinity, sync the units from Action Plan to Daily Log
                    if selected_param == "Alkalinity":
                        self.log_alk_unit.set(self.alkalinity_unit.get())
        except (ValueError, KeyError):
            pass  # Invalid input or other error, don't populate

    def populate_daily_log_from_consumption(self, *args):
        """Auto-populate daily log when user enters end value in Consumption Calculator"""
        try:
            end_val = self.cons_end.get().strip()
            selected_param = self.cons_parameter.get()
            
            if end_val and selected_param in self.log_variables:
                # Parse the value to make sure it's valid
                test_val = float(end_val)  # Validate it's a number
                
                # Only populate if the log field is currently empty (don't overwrite user data)
                current_log_val = self.log_variables[selected_param].get().strip()
                if not current_log_val:
                    # Set the full value, not just validation result
                    self.log_variables[selected_param].set(end_val)
                    
                    # For alkalinity, sync the units from Consumption Calculator to Daily Log
                    if selected_param == "Alkalinity":
                        self.log_alk_unit.set(self.cons_alk_unit.get())
        except (ValueError, KeyError):
            pass  # Invalid input or other error, don't populate

    def auto_cons_start_unit_detection(self, *args):
        """Automatically detect alkalinity units for consumption start value"""
        if self.cons_parameter.get() == "Alkalinity":
            try:
                val_str = self.cons_start.get().strip()
                if val_str:
                    val = float(val_str)
                    # Same improved logic
                    if val > 50 and self.cons_alk_unit.get() == "dKH":
                        self.cons_alk_unit.set("ppm")
                    elif val <= 20 and self.cons_alk_unit.get() == "ppm":
                        self.cons_alk_unit.set("dKH")
            except ValueError:
                pass

    def auto_cons_end_unit_detection(self, *args):
        """Automatically detect alkalinity units for consumption end value"""
        if self.cons_parameter.get() == "Alkalinity":
            try:
                val_str = self.cons_end.get().strip()
                if val_str:
                    val = float(val_str)
                    # Same improved logic
                    if val > 50 and self.cons_alk_unit.get() == "dKH":
                        self.cons_alk_unit.set("ppm")
                    elif val <= 20 and self.cons_alk_unit.get() == "ppm":
                        self.cons_alk_unit.set("dKH")
            except ValueError:
                pass

    def update_target_by_unit(self, *args):
        """Update target value when alkalinity unit changes"""
        if self.selected_parameter.get() == "Alkalinity":
            if self.alkalinity_unit.get() == "ppm":
                self.target_value.set("152")  # 8.5 dKH * 17.86
            else:
                self.target_value.set("8.5")

    def toggle_custom_visibility(self, *args):
        """Show/hide custom concentration field based on brand selection"""
        if self.selected_brand.get() == "Custom":
            self.custom_frame.pack(side="left", padx=10)
        else:
            self.custom_frame.pack_forget()

    def toggle_maint_custom_visibility(self, *args):
        """Show/hide custom concentration field for maintenance tab"""
        if self.cons_brand.get() == "Custom":
            self.maint_custom_frame.pack(side="left", padx=10)
        else:
            self.maint_custom_frame.pack_forget()

    def sync_action_ui(self, *args):
        """Synchronize Action Plan UI when parameter changes"""
        param = self.selected_parameter.get()
        brands = list(self.param_config[param]["dosing"].keys())
        
        self.brand_combo['values'] = brands
        self.selected_brand.set(brands[0])
        self.custom_label.config(text=self.param_config[param]["custom_unit"])
        
        # Show alkalinity unit selector only for alkalinity
        if param == "Alkalinity":
            self.alk_unit_frame.pack(side="left")
        else:
            self.alk_unit_frame.pack_forget()
            self.target_value.set(str(self.param_config[param]["target"]))

    def sync_maintenance_ui(self, *args):
        """Synchronize Maintenance UI when parameter changes"""
        param = self.cons_parameter.get()
        
        # Debug: Print what parameter we're switching to
        print(f"DEBUG: Switching to parameter: {param}")
        
        if param not in self.param_config:
            print(f"DEBUG: Parameter {param} not found in config")
            return
            
        brands = list(self.param_config[param]["dosing"].keys())
        print(f"DEBUG: Available brands for {param}: {brands}")
        
        # Update the brand dropdown with new values
        self.cons_brand_combo['values'] = brands
        if brands:  # Make sure we have brands to set
            self.cons_brand.set(brands[0])
            print(f"DEBUG: Set brand to: {brands[0]}")
        
        # Update custom label
        self.maint_custom_label.config(text=self.param_config[param]["custom_unit"])
        
        # Show alkalinity unit selector only for alkalinity
        if param == "Alkalinity":
            self.cons_alk_frame.pack(side="left")
        else:
            self.cons_alk_frame.pack_forget()

    def build_action_plan(self):
        """Build the Action Plan tab with safety calculator"""
        frame = self.tabs["Action Plan"]
        
        # System Configuration
        config_frame = ttk.LabelFrame(frame, text=" 1. System Configuration ", padding=10)
        config_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(config_frame, text="Tank Volume:").pack(side="left")
        volume_entry = tk.Entry(config_frame, textvariable=self.tank_volume, width=8)
        volume_entry.pack(side="left", padx=5)
        
        ttk.Radiobutton(config_frame, text="Gallons", variable=self.volume_unit, value="Gallons").pack(side="left", padx=5)
        ttk.Radiobutton(config_frame, text="Liters", variable=self.volume_unit, value="Liters").pack(side="left")

        # Product Selection
        product_frame = ttk.LabelFrame(frame, text=" 2. Product Selection ", padding=10)
        product_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(product_frame, text="Parameter:").pack(side="left")
        param_combo = ttk.Combobox(product_frame, textvariable=self.selected_parameter, 
                                  values=list(self.param_config.keys()), state="readonly", width=12)
        param_combo.pack(side="left", padx=5)
        
        tk.Label(product_frame, text="Brand:").pack(side="left", padx=(20,5))
        self.brand_combo = ttk.Combobox(product_frame, textvariable=self.selected_brand, 
                                       state="readonly", width=15)
        self.brand_combo.pack(side="left", padx=5)
        
        # Custom concentration frame (shown when Custom brand selected)
        self.custom_frame = ttk.Frame(product_frame)
        tk.Label(self.custom_frame, text="Concentration:").pack(side="left", padx=(10,5))
        tk.Entry(self.custom_frame, textvariable=self.custom_strength, width=8).pack(side="left")
        self.custom_label = tk.Label(self.custom_frame, text="unit")
        self.custom_label.pack(side="left", padx=(5,0))

        # Safety Calculator - Responsive multi-row layout
        calc_frame = ttk.LabelFrame(frame, text=" 3. Safety Calculator ", padding=10)
        calc_frame.pack(fill="x", padx=20, pady=5)
        
        # Row 1: Current and Target Values
        calc_row1 = ttk.Frame(calc_frame)
        calc_row1.pack(fill="x", pady=2)
        
        tk.Label(calc_row1, text="Current Value:").pack(side="left")
        tk.Entry(calc_row1, textvariable=self.current_value, width=10).pack(side="left", padx=5)
        
        tk.Label(calc_row1, text="Target Value:").pack(side="left", padx=(20,5))
        tk.Entry(calc_row1, textvariable=self.target_value, width=10).pack(side="left", padx=5)
        
        tk.Label(calc_row1, text="pH (optional):").pack(side="left", padx=(20,5))
        tk.Entry(calc_row1, textvariable=self.ph_value, width=8).pack(side="left", padx=5)
        
        # Row 2: Alkalinity units (only shown for alkalinity parameter)
        calc_row2 = ttk.Frame(calc_frame)
        calc_row2.pack(fill="x", pady=2)
        
        self.alk_unit_frame = ttk.Frame(calc_row2)
        tk.Label(self.alk_unit_frame, text="Alkalinity Unit:").pack(side="left")
        ttk.Radiobutton(self.alk_unit_frame, text="dKH", variable=self.alkalinity_unit, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(self.alk_unit_frame, text="ppm", variable=self.alkalinity_unit, value="ppm").pack(side="left")

        # Calculate button and results
        tk.Button(frame, text="GENERATE SAFETY PLAN", command=self.calculate_dosing_plan, 
                 bg="#2c3e50", fg="white", font=('Arial', 10, 'bold')).pack(pady=15)
        
        # Results with scrollable text widget for long results
        result_frame = ttk.Frame(frame)
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0,10))
        
        self.result_text = tk.Text(result_frame, height=8, wrap=tk.WORD, font=("Arial", 10))
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_scrollbar.set)
        
        self.result_text.pack(side="left", fill="both", expand=True)
        result_scrollbar.pack(side="right", fill="y")
        
        # Initial message
        self.result_text.insert("1.0", "Enter values above and click 'Generate Safety Plan' to see dosing recommendations.")
        self.result_text.config(state="disabled")  # Make read-only
        
        # Tab Explanation Section - MOVED TO BOTTOM
        help_frame = ttk.LabelFrame(frame, text=" ℹ️ How to Use Action Plan ", padding=10)
        help_frame.pack(fill="x", padx=20, pady=(10,20))
        
        help_text = ("This tab calculates safe dosing schedules to change your reef parameters. "
                    "Enter your tank volume, select the parameter you want to adjust, "
                    "choose your dosing product, then enter current and target values. "
                    "The safety calculator will create a multi-day dosing plan that prevents shocking your corals.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg="#2c3e50").pack(anchor="w")

    def build_maintenance(self):
        """Build the Maintenance tab with consumption tracker and logging"""
        frame = self.tabs["Maintenance"]
        
        # Tab Explanation Section
        help_frame = ttk.LabelFrame(frame, text=" ℹ️ How to Use Maintenance ", padding=10)
        help_frame.pack(fill="x", padx=20, pady=5)
        
        help_text = ("Track your reef's consumption rates and log daily test results. "
                    "The consumption calculator helps you understand how much your tank uses each day "
                    "by comparing start/end values over time. The daily test log keeps a record of "
                    "all your measurements for trend analysis.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg="#2c3e50").pack(anchor="w")
        
        # Combined Consumption Rate Calculator with Tank Configuration
        cons_frame = ttk.LabelFrame(frame, text=" Consumption Rate Calculator ", padding=15)
        cons_frame.pack(fill="x", padx=20, pady=5)
        
        # Row 1: Tank Volume (integrated into calculator)
        tank_row = ttk.Frame(cons_frame)
        tank_row.pack(fill="x", pady=5)
        
        tk.Label(tank_row, text="Tank Volume:", width=12, anchor="w").pack(side="left")
        volume_entry = tk.Entry(tank_row, textvariable=self.tank_volume, width=10)
        volume_entry.pack(side="left", padx=5)
        
        ttk.Radiobutton(tank_row, text="Gallons", variable=self.volume_unit, value="Gallons").pack(side="left", padx=5)
        ttk.Radiobutton(tank_row, text="Liters", variable=self.volume_unit, value="Liters").pack(side="left", padx=5)
        
        tk.Label(tank_row, text="(synced with Action Plan)", font=("Arial", 8), fg="gray").pack(side="left", padx=10)
        
        # Row 2: Parameter and Brand Selection
        param_row = ttk.Frame(cons_frame)
        param_row.pack(fill="x", pady=5)
        
        tk.Label(param_row, text="Parameter:", width=12, anchor="w").pack(side="left")
        cons_param_combo = ttk.Combobox(param_row, textvariable=self.cons_parameter, 
                                       values=list(self.param_config.keys()), state="readonly", width=15)
        cons_param_combo.pack(side="left", padx=5)
        
        tk.Label(param_row, text="Dosing Product:", width=15, anchor="w").pack(side="left", padx=(20,5))
        self.cons_brand_combo = ttk.Combobox(param_row, textvariable=self.cons_brand, 
                                            state="readonly", width=18)
        self.cons_brand_combo.pack(side="left", padx=5)
        
        # Row 3: Custom concentration (appears when Custom selected)
        self.maint_custom_frame = ttk.Frame(cons_frame)
        self.maint_custom_frame.pack(fill="x", pady=5)
        
        tk.Label(self.maint_custom_frame, text="Custom Conc:", width=12, anchor="w").pack(side="left")
        tk.Entry(self.maint_custom_frame, textvariable=self.maint_custom_strength, width=10).pack(side="left", padx=5)
        self.maint_custom_label = tk.Label(self.maint_custom_frame, text="unit", width=15, anchor="w")
        self.maint_custom_label.pack(side="left", padx=5)

        # Row 4: Test Values Input
        values_row = ttk.Frame(cons_frame)
        values_row.pack(fill="x", pady=5)
        
        tk.Label(values_row, text="Start Value:", width=12, anchor="w").pack(side="left")
        tk.Entry(values_row, textvariable=self.cons_start, width=10).pack(side="left", padx=5)
        
        tk.Label(values_row, text="End Value:", width=12, anchor="w").pack(side="left", padx=(20,5))
        tk.Entry(values_row, textvariable=self.cons_end, width=10).pack(side="left", padx=5)
        
        tk.Label(values_row, text="Days:", width=8, anchor="w").pack(side="left", padx=(20,5))
        tk.Entry(values_row, textvariable=self.cons_days, width=6).pack(side="left", padx=5)

        # Row 5: Alkalinity units (shown only for alkalinity) and Calculate button
        calc_row = ttk.Frame(cons_frame)
        calc_row.pack(fill="x", pady=10)
        
        self.cons_alk_frame = ttk.Frame(calc_row)
        self.cons_alk_frame.pack(side="left")
        tk.Label(self.cons_alk_frame, text="Units:", width=12, anchor="w").pack(side="left")
        ttk.Radiobutton(self.cons_alk_frame, text="dKH", variable=self.cons_alk_unit, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(self.cons_alk_frame, text="ppm", variable=self.cons_alk_unit, value="ppm").pack(side="left", padx=5)

        # Calculate button positioned closer to units (not far right)
        tk.Button(calc_row, text="CALCULATE CONSUMPTION RATE", command=self.calculate_consumption_rate, 
                 bg="#16a085", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=20)

        # Daily Logging Section (unchanged)
        log_frame = ttk.LabelFrame(frame, text=" Daily Test Log ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(5,20))
        
        self.log_variables = {param: tk.StringVar() for param in self.param_config.keys()}
        self.log_alk_unit = tk.StringVar(value="dKH")
        
        # Create entry fields for each parameter
        for param in self.param_config.keys():
            row_frame = ttk.Frame(log_frame)
            row_frame.pack(fill="x", pady=3)
            
            # Parameter label with consistent width
            tk.Label(row_frame, text=param, width=15, anchor="w").pack(side="left")
            
            # Value entry
            entry = tk.Entry(row_frame, textvariable=self.log_variables[param], width=12)
            entry.pack(side="left", padx=(0,10))
            
            # Unit handling - dynamic for alkalinity, static for others
            if param == "Alkalinity":
                # Dynamic unit selector for alkalinity
                unit_frame = ttk.Frame(row_frame)
                unit_frame.pack(side="left")
                
                ttk.Radiobutton(unit_frame, text="dKH", variable=self.log_alk_unit, value="dKH").pack(side="left", padx=5)
                ttk.Radiobutton(unit_frame, text="ppm", variable=self.log_alk_unit, value="ppm").pack(side="left", padx=5)
                
                # Add auto-detection for alkalinity logging
                self.log_variables[param].trace_add("write", self.auto_log_unit_detection)
            else:
                # Static unit label for other parameters
                unit_text = self.param_config[param]["unit"]
                tk.Label(row_frame, text=unit_text, width=8, anchor="w").pack(side="left")
        
        tk.Button(log_frame, text="SAVE TO LOG", command=self.save_test_entry, 
                 bg="#27ae60", fg="white", font=('Arial', 10, 'bold')).pack(pady=15)

    def build_trends(self):
        """Build the Trends tab with normal layout (no individual scrolling)"""
        frame = self.tabs["Trends"]
        
        # Refresh button at top
        tk.Button(frame, text="REFRESH GRAPHS", command=self.draw_parameter_graphs, 
                 bg="#3498db", fg="white", font=('Arial', 10, 'bold')).pack(pady=10)
        
        # Chart container (no individual scrolling - let tab handle it)
        self.chart_frame = ttk.Frame(frame)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tab Explanation Section - MOVED TO BOTTOM
        help_frame = ttk.LabelFrame(frame, text=" ℹ️ How to Use Trends ", padding=10)
        help_frame.pack(fill="x", padx=20, pady=(10,20))
        
        help_text = ("Visualize your reef parameters over time with automatic trend graphs. "
                    "Each parameter gets its own chart showing your test results, target ranges (green shading), "
                    "and ideal values (green line). Use these graphs to spot trends, verify stability, "
                    "and track the effectiveness of your dosing programs.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg="#2c3e50").pack(anchor="w")

    def build_history(self):
        """Build the History tab with test kit instructions and data management"""
        frame = self.tabs["History"]
        
        # Test Kit Instructions
        kit_frame = ttk.LabelFrame(frame, text=" Test Kit Instructions & Timer ", padding=15)
        kit_frame.pack(fill="x", padx=20, pady=5)
        
        # Parameter and kit selection
        selection_frame = ttk.Frame(kit_frame)
        selection_frame.pack(fill="x", pady=(0,10))
        
        self.hist_parameter = tk.StringVar(value="Alkalinity")
        self.hist_kit = tk.StringVar()
        
        tk.Label(selection_frame, text="Parameter:").pack(side="left")
        param_combo = ttk.Combobox(selection_frame, textvariable=self.hist_parameter, 
                                  values=list(self.param_config.keys()), state="readonly", width=12)
        param_combo.pack(side="left", padx=(5,20))
        
        tk.Label(selection_frame, text="Test Kit:").pack(side="left")
        self.kit_combo = ttk.Combobox(selection_frame, textvariable=self.hist_kit, 
                                     state="readonly", width=15)
        self.kit_combo.pack(side="left", padx=(5,20))
        
        # Timer display with improved functionality
        timer_frame = ttk.Frame(selection_frame)
        timer_frame.pack(side="right", padx=20)
        
        tk.Label(timer_frame, text="Test Timer:", font=("Arial", 9)).pack()
        self.timer_label = tk.Label(timer_frame, text="00:00", font=("Arial", 18, "bold"), 
                                   fg="#e67e22", cursor="hand2", relief="ridge", bd=2, padx=10, pady=5)
        self.timer_label.pack()
        self.timer_label.bind("<Button-1>", self.cancel_timer)
        
        tk.Label(timer_frame, text="Click timer to cancel/reset", font=("Arial", 7), fg="gray").pack()

        # Dynamic checklist area (no individual scrolling)
        self.checklist_frame = ttk.Frame(kit_frame)
        self.checklist_frame.pack(fill="x", pady=10)
        
        # Set up traces for history tab
        self.hist_parameter.trace_add("write", self.sync_history_kits)
        self.hist_kit.trace_add("write", self.draw_test_checklist)

        # Data History Table (no individual scrolling)
        history_frame = ttk.LabelFrame(frame, text=" Test History ", padding=10)
        history_frame.pack(fill="both", expand=True, padx=20, pady=(5,10))
        
        # Create treeview with better column headers
        self.history_tree = ttk.Treeview(history_frame, columns=("ID", "Timestamp", "Parameter", "Value"), 
                                        show="headings", height=12)
        
        # Configure column headers and widths
        self.history_tree.heading("ID", text="ID")
        self.history_tree.heading("Timestamp", text="Date & Time")
        self.history_tree.heading("Parameter", text="Parameter")  
        self.history_tree.heading("Value", text="Value")
        
        # Hide ID column but keep it for deletions
        self.history_tree['displaycolumns'] = ("Timestamp", "Parameter", "Value")
        
        # Set column widths
        self.history_tree.column("Timestamp", width=150)
        self.history_tree.column("Parameter", width=120)
        self.history_tree.column("Value", width=100)
        
        # Add scrollbar for history table only
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add double-click editing and right-click context menu
        self.history_tree.bind("<Double-1>", self.edit_history_entry)
        self.history_tree.bind("<Button-3>", self.show_context_menu)  # Right-click
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit Entry", command=self.edit_history_entry)
        self.context_menu.add_command(label="Delete Entry", command=self.delete_selected_row)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Export to CSV", command=self.export_data_to_csv)
        
        # Control buttons (simplified - removed delete button since it's in context menu)
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(button_frame, text="EXPORT TO CSV", command=self.export_data_to_csv, 
                 bg="#8e44ad", fg="white").pack(side="left")
        
        tk.Button(button_frame, text="REFRESH HISTORY", command=self.refresh_history_display, 
                 bg="#34495e", fg="white").pack(side="left", padx=10)
        
        tk.Label(button_frame, text="💡 Double-click to edit • Right-click for menu", 
                font=("Arial", 8), fg="gray").pack(side="right")
        
        # Initialize history display
        self.sync_history_kits()
        self.refresh_history_display()
        
        # Tab Explanation Section - MOVED TO BOTTOM
        help_frame = ttk.LabelFrame(frame, text=" ℹ️ How to Use History ", padding=10)
        help_frame.pack(fill="x", padx=20, pady=(10,20))
        
        help_text = ("Get step-by-step testing instructions for popular reef test kits, complete with built-in timers. "
                    "Choose your parameter and test kit brand for detailed procedures based on manufacturer manuals. "
                    "The test history section below lets you view, edit (double-click), and manage all your logged data. "
                    "Right-click entries for quick actions like editing or deleting.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg="#2c3e50").pack(anchor="w")

    def sync_history_kits(self, *args):
        """Update available test kits when parameter selection changes"""
        param = self.hist_parameter.get()
        kits = list(self.param_config[param]["kits"].keys())
        self.kit_combo['values'] = kits
        if kits:
            self.hist_kit.set(kits[0])

    def draw_test_checklist(self, *args):
        """Draw the dynamic test kit checklist with checkboxes and strikethrough"""
        # Clear existing checklist
        for widget in self.checklist_frame.winfo_children():
            widget.destroy()
            
        param = self.hist_parameter.get()
        kit = self.hist_kit.get()
        
        if not kit:
            return
            
        instructions = self.param_config[param]["kits"].get(kit, [])
        
        # Store checkbox states and label references
        if not hasattr(self, 'checkbox_states'):
            self.checkbox_states = {}
        if not hasattr(self, 'step_labels'):
            self.step_labels = {}
        
        # Clear states for new checklist
        self.checkbox_states.clear()
        self.step_labels.clear()
        
        for i, step in enumerate(instructions):
            step_frame = ttk.Frame(self.checklist_frame)
            step_frame.pack(anchor="w", pady=3, fill="x")
            
            # Step text formatting
            step_text = step.replace(f"{i+1}. ", "")  # Remove number since we'll add it
            full_text = f"Step {i+1}: {step_text}"
            
            # Create checkbox with callback
            checkbox_var = tk.BooleanVar()
            self.checkbox_states[i] = checkbox_var
            
            checkbox = tk.Checkbutton(step_frame, variable=checkbox_var, font=('Arial', 9),
                                    command=lambda idx=i: self.toggle_step_completion(idx))
            checkbox.pack(side="left")
            
            # Step label that can be modified
            step_label = tk.Label(step_frame, text=full_text, 
                                 font=('Arial', 9), wraplength=500, justify="left", anchor="w")
            step_label.pack(side="left", padx=(5,0), fill="x", expand=True, anchor="w")
            
            # Store label reference
            self.step_labels[i] = step_label
            
            # Enhanced timer detection - look for time periods
            time_patterns = [
                (r'(\d+)\s*min(?:ute)?s?', lambda m: int(m.group(1))),      # "3 mins", "3 minutes"
                (r'exactly\s+(\d+)\s*min', lambda m: int(m.group(1))),       # "exactly 3 mins"
                (r'wait.*?(\d+).*?min', lambda m: int(m.group(1))),          # "wait 3 mins"
                (r'(\d+).*?min.*?development', lambda m: int(m.group(1))),   # "3 mins for development"
                (r'(\d+).*?min.*?color', lambda m: int(m.group(1))),         # "3 mins color development"
            ]
            
            timer_minutes = None
            for pattern, extract_func in time_patterns:
                match = re.search(pattern, step.lower())
                if match:
                    try:
                        timer_minutes = extract_func(match)
                        break
                    except (ValueError, AttributeError):
                        continue
            
            # Add timer button if time period found - positioned on the right
            if timer_minutes and timer_minutes > 0:
                timer_btn = tk.Button(step_frame, 
                                    text=f"{timer_minutes} MIN TIMER", 
                                    command=lambda m=timer_minutes: self.start_simple_timer(m),
                                    bg="#e67e22", fg="white", 
                                    font=("Arial", 8, "bold"),
                                    relief="raised", bd=2)
                timer_btn.pack(side="right", padx=10)

    def toggle_step_completion(self, step_index):
        """Toggle strikethrough when checkbox is clicked"""
        if step_index in self.checkbox_states and step_index in self.step_labels:
            is_checked = self.checkbox_states[step_index].get()
            label = self.step_labels[step_index]
            
            if is_checked:
                # Add strikethrough by changing font
                current_text = label.cget("text")
                label.config(font=('Arial', 9, 'overstrike'), fg="gray")
            else:
                # Remove strikethrough 
                label.config(font=('Arial', 9), fg="black")
                
                # Add tooltip-like text for timer
                timer_info = tk.Label(step_frame, text=f"← Click to start {timer_minutes}min timer", 
                                    font=("Arial", 7), fg="gray")
                timer_info.pack(side="right", padx=(0,5))

    def start_simple_timer(self, minutes):
        """Start a simple click-to-cancel countdown timer"""
        if self.timer_running:
            # If timer is running, cancel it
            self.cancel_timer()
            return
            
        # Start new timer
        self.timer_running = True
        self.timer_start_time = datetime.now()
        self.timer_duration = timedelta(minutes=minutes)
        self.timer_end_time = self.timer_start_time + self.timer_duration
        
        # Update timer display immediately
        self.timer_label.config(text=f"{minutes:02d}:00", fg="#e67e22")
        
        # Start the countdown
        self.update_timer_display()
        
        # Show user feedback
        self.timer_label.config(cursor="hand2")
        
    def update_timer_display(self):
        """Update the timer display every second"""
        if not self.timer_running:
            return
            
        now = datetime.now()
        remaining = self.timer_end_time - now
        
        if remaining.total_seconds() > 0:
            # Timer still running
            mins, secs = divmod(int(remaining.total_seconds()), 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}", fg="#e67e22")
            
            # Schedule next update
            self.timer_after_id = self.root.after(1000, self.update_timer_display)
        else:
            # Timer finished
            self.timer_finished()
    
    def timer_finished(self):
        """Handle timer completion"""
        self.timer_running = False
        self.timer_after_id = None
        
        # Flash the timer and show completion
        self.timer_label.config(text="DONE!", fg="red", font=("Arial", 16, "bold"))
        
        # Show completion message
        messagebox.showinfo("Timer Complete", 
                          "⏰ Test timer completed!\n\nYour sample is ready to read.\n\n"
                          "Click the timer to reset it.")
        
        # Auto-reset after showing message
        self.root.after(2000, lambda: self.timer_label.config(text="00:00", fg="#e67e22", 
                                                             font=("Arial", 16, "bold")))

    def cancel_timer(self, event=None):
        """Cancel/reset the running timer (simplified click-to-cancel)"""
        if self.timer_running:
            self.timer_running = False
            if self.timer_after_id:
                self.root.after_cancel(self.timer_after_id)
                self.timer_after_id = None
            
        # Reset display
        self.timer_label.config(text="00:00", fg="#e67e22", font=("Arial", 16, "bold"))

    def calculate_dosing_plan(self):
        """Calculate safe dosing plan with comprehensive validation"""
        try:
            # Input validation
            param = self.selected_parameter.get()
            
            # Validate tank volume
            is_valid, error_msg = self.validate_numeric_input(self.tank_volume.get(), 1, 10000)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"Tank Volume: {error_msg}")
                return
                
            volume_gallons = float(self.tank_volume.get())
            if self.volume_unit.get() == "Gallons":
                volume_liters = volume_gallons * self.LITERS_PER_GALLON
            else:
                volume_liters = volume_gallons
                volume_gallons = volume_liters / self.LITERS_PER_GALLON
            
            # Validate current and target values
            is_valid, error_msg = self.validate_numeric_input(self.current_value.get(), 0)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"Current Value: {error_msg}")
                return
                
            is_valid, error_msg = self.validate_numeric_input(self.target_value.get(), 0)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"Target Value: {error_msg}")
                return
            
            current_val = float(self.current_value.get())
            target_val = float(self.target_value.get())
            
            # Validate pH if provided
            if self.ph_value.get():
                is_valid, error_msg = self.validate_numeric_input(self.ph_value.get(), 6.0, 10.0)
                if not is_valid:
                    messagebox.showerror("Invalid Input", f"pH Value: {error_msg}")
                    return
            
            # Calculate difference in standard units
            if param == "Alkalinity" and self.alkalinity_unit.get() == "ppm":
                # Convert ppm difference to dKH for calculation
                difference = (target_val - current_val) / self.DKH_TO_PPM_FACTOR
            else:
                difference = target_val - current_val
            
            if abs(difference) < 0.01:
                self.result_label.config(text="Current and target values are essentially the same. No dosing needed.")
                return
            
            # Get dosing strength
            if self.selected_brand.get() == "Custom":
                is_valid, error_msg = self.validate_numeric_input(self.custom_strength.get(), 0.01)
                if not is_valid:
                    messagebox.showerror("Invalid Input", f"Custom Strength: {error_msg}")
                    return
                strength = float(self.custom_strength.get())
            else:
                strength = self.param_config[param]["dosing"][self.selected_brand.get()]
            
            # Calculate total dose needed (in mL)
            total_dose_ml = (difference * volume_liters) / strength
            
            # Determine safe dosing schedule
            max_daily_change = self.param_config[param]["max_daily"]
            days_needed = max(1, int(abs(difference) / max_daily_change) + 1)
            
            # Special considerations for alkalinity and pH
            if param == "Alkalinity" and self.ph_value.get():
                ph = float(self.ph_value.get())
                if ph > 8.3:
                    days_needed = max(days_needed, 3)
                    ph_warning = " (Extended due to high pH - alkalinity raises pH)"
                else:
                    ph_warning = ""
            else:
                ph_warning = ""
            
            daily_dose_ml = total_dose_ml / days_needed
            
            # Format results
            if difference > 0:
                action = "INCREASE"
                dose_direction = "Add"
            else:
                action = "DECREASE" 
                dose_direction = "Reduce by"
                total_dose_ml = abs(total_dose_ml)
                daily_dose_ml = abs(daily_dose_ml)
            
            # Create detailed result message
            result_text = f"""SAFETY DOSING PLAN - {action} {param}

Tank: {volume_gallons:.0f} gallons ({volume_liters:.1f}L)
Change needed: {current_val} → {target_val} {self.alkalinity_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit']}
Product: {self.selected_brand.get()}

RECOMMENDED SCHEDULE{ph_warning}:
• Total dose needed: {total_dose_ml:.1f} mL
• {dose_direction}: {daily_dose_ml:.1f} mL per day
• Duration: {days_needed} days
• Test daily and adjust as needed

⚠️  SAFETY REMINDERS:
• Always test before dosing
• Dose slowly over several hours when possible  
• Monitor coral response carefully
• Stop dosing if any adverse effects observed"""

            # Display result in scrollable text widget
            self.result_text.config(state="normal")  # Enable editing
            self.result_text.delete("1.0", tk.END)   # Clear existing content
            self.result_text.insert("1.0", result_text)  # Insert new result
            self.result_text.config(state="disabled")  # Make read-only again
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Please check all inputs are valid numbers.\n\nError: {str(e)}")

    def calculate_consumption_rate(self):
        """Calculate daily consumption rate with input validation"""
        try:
            # Validate all inputs
            param = self.cons_parameter.get()
            
            is_valid, error_msg = self.validate_numeric_input(self.cons_start.get(), 0)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"Start Value: {error_msg}")
                return
                
            is_valid, error_msg = self.validate_numeric_input(self.cons_end.get(), 0)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"End Value: {error_msg}")
                return
                
            is_valid, error_msg = self.validate_numeric_input(self.cons_days.get(), 0.1)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"Days: {error_msg}")
                return
            
            # Get tank volume
            is_valid, error_msg = self.validate_numeric_input(self.tank_volume.get(), 1, 10000)
            if not is_valid:
                messagebox.showerror("Invalid Input", f"Tank Volume: {error_msg}")
                return
                
            start_val = float(self.cons_start.get())
            end_val = float(self.cons_end.get())
            days = float(self.cons_days.get())
            
            volume_gallons = float(self.tank_volume.get())
            volume_liters = volume_gallons * self.LITERS_PER_GALLON if self.volume_unit.get() == "Gallons" else volume_gallons
            
            # Check if values make sense (start should typically be higher than end)
            if start_val < end_val:
                response = messagebox.askyesno("Unusual Values", 
                    f"Your end value ({end_val}) is higher than start value ({start_val}).\n"
                    f"This suggests the parameter increased rather than decreased.\n"
                    f"Continue with calculation?")
                if not response:
                    return
            
            # Calculate daily consumption
            total_change = start_val - end_val
            daily_change = total_change / days
            
            # Convert to standard units if needed
            if param == "Alkalinity" and self.cons_alk_unit.get() == "ppm":
                daily_change_standard = daily_change / self.DKH_TO_PPM_FACTOR
            else:
                daily_change_standard = daily_change
            
            # Get dosing strength
            if self.cons_brand.get() == "Custom":
                is_valid, error_msg = self.validate_numeric_input(self.maint_custom_strength.get(), 0.01)
                if not is_valid:
                    messagebox.showerror("Invalid Input", f"Custom Strength: {error_msg}")
                    return
                strength = float(self.maint_custom_strength.get())
            else:
                strength = self.param_config[param]["dosing"][self.cons_brand.get()]
            
            # Calculate required dosing in mL/day
            daily_dose_ml = (daily_change_standard * volume_liters) / strength
            
            # Show result in popup instead of persistent display
            if daily_change > 0:
                trend = "consumed"
                message = f"Daily consumption: {abs(daily_dose_ml):.1f} mL/day needed\n\n"
                message += f"Parameter decreased by {daily_change:.2f} {self.cons_alk_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit']} per day"
            elif daily_change < 0:
                trend = "increased"  
                message = f"Parameter increasing: {abs(daily_dose_ml):.1f} mL/day equivalent\n\n"
                message += f"Parameter increased by {abs(daily_change):.2f} {self.cons_alk_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit']} per day"
            else:
                trend = "stable"
                message = f"Parameter stable: 0.0 mL/day\n\nNo change detected over the test period"
            
            messagebox.showinfo("Consumption Rate Result", message)
            
        except Exception as e:
            messagebox.showerror("Calculation Error", f"Please check all inputs.\n\nError: {str(e)}")

    def save_test_entry(self):
        """Save test results to database with proper unit handling"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            entries_saved = 0
            
            for param, var in self.log_variables.items():
                value_str = var.get().strip()
                if value_str:  # Only save non-empty values
                    # Validate the input
                    is_valid, error_msg = self.validate_numeric_input(value_str, 0)
                    if not is_valid:
                        messagebox.showerror("Invalid Input", f"{param}: {error_msg}")
                        conn.close()
                        return
                    
                    value = float(value_str)
                    
                    # Convert alkalinity to consistent storage format (always store as actual measured value)
                    # Note: Fixed the unit conversion issue - store what was actually measured
                    if param == "Alkalinity":
                        # Store with unit information to avoid confusion later
                        unit_suffix = f" ({self.log_alk_unit.get()})"
                        param_with_unit = f"{param}{unit_suffix}"
                    else:
                        param_with_unit = param
                        unit_suffix = f" ({self.param_config[param]['unit']})"
                        param_with_unit = f"{param}{unit_suffix}"
                    
                    # Save to database
                    cursor.execute('INSERT INTO logs (timestamp, parameter, value) VALUES (?, ?, ?)', 
                                 (timestamp, param_with_unit, value))
                    
                    # Clear the entry field
                    var.set("")
                    entries_saved += 1
            
            if entries_saved > 0:
                conn.commit()
                conn.close()
                self.refresh_history_display()
                
                # Change button text to show success (no popup)
                self.save_button.config(text="SAVED", bg="#2ecc71")
                self.root.after(2000, self.reset_save_button)  # Reset after 2 seconds
            else:
                conn.close()
                # Change button text to show warning (no popup)
                self.save_button.config(text="NO DATA", bg="#f39c12")
                self.root.after(2000, self.reset_save_button)  # Reset after 2 seconds
                
        except Exception as e:
            # Show error on button instead of popup
            self.save_button.config(text="ERROR", bg="#e74c3c")
            self.root.after(2000, self.reset_save_button)  # Reset after 2 seconds

    def reset_save_button(self):
        """Reset save button to original state"""
        self.save_button.config(text="SAVE TO LOG", bg="#27ae60")

    def draw_parameter_graphs(self):
        """Draw trend graphs that scale to fit window width with proper scrolling"""
        # Clear existing charts
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        if not os.path.exists(self.db_path):
            tk.Label(self.chart_frame, text="No data available. Add some test results first!", 
                    font=('Arial', 12)).pack(pady=50)
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Read data with better column names
            df = pd.read_sql_query('''
                SELECT timestamp as Date, parameter as Parameter, value as Value 
                FROM logs 
                ORDER BY timestamp
            ''', conn, parse_dates=["Date"])
            
            conn.close()
            
            if df.empty:
                tk.Label(self.chart_frame, text="No data available. Add some test results first!", 
                        font=('Arial', 12)).pack(pady=50)
                return
            
            # Get current window width to scale charts appropriately
            self.chart_frame.update_idletasks()
            try:
                canvas_width = self.tab_canvases["Trends"].winfo_width()
                # Convert pixels to inches (roughly 100 pixels per inch)
                chart_width = max(6, (canvas_width - 100) / 100)  # Minimum 6 inches, scale with window
            except:
                chart_width = 8  # Default fallback
            
            # Create properly sized subplots that fit the window
            num_params = len(self.param_config)
            min_height_per_chart = 3  # Slightly smaller for better fit
            total_height = min_height_per_chart * num_params
            
            fig, axes = plt.subplots(num_params, 1, figsize=(chart_width, total_height), 
                                   constrained_layout=True)
            if num_params == 1:
                axes = [axes]  # Make it a list for consistency
            
            fig.suptitle('Reef Parameter Trends', fontsize=14, fontweight='bold')
            
            for i, param in enumerate(self.param_config.keys()):
                ax = axes[i]
                
                # Filter data for this parameter (handle both with and without units in storage)
                param_data = df[df['Parameter'].str.contains(param, regex=False)].copy()
                
                if not param_data.empty:
                    # Sort by date
                    param_data = param_data.sort_values('Date')
                    
                    # Smart alkalinity unit detection
                    if param == "Alkalinity":
                        # Analyze the data to determine if it's dKH or ppm
                        avg_value = param_data['Value'].mean()
                        if avg_value > 50:  # Likely ppm (typically 120-180)
                            display_unit = "ppm"
                            target_low = self.param_config[param]['low'] * self.DKH_TO_PPM_FACTOR
                            target_high = self.param_config[param]['high'] * self.DKH_TO_PPM_FACTOR
                            target_value = self.param_config[param]['target'] * self.DKH_TO_PPM_FACTOR
                        else:  # Likely dKH (typically 7-12)
                            display_unit = "dKH"
                            target_low = self.param_config[param]['low']
                            target_high = self.param_config[param]['high']
                            target_value = self.param_config[param]['target']
                    else:
                        # Use standard units for other parameters
                        display_unit = self.param_config[param]['unit']
                        target_low = self.param_config[param]['low']
                        target_high = self.param_config[param]['high']
                        target_value = self.param_config[param]['target']
                    
                    # Plot the data with good spacing
                    ax.plot(param_data['Date'], param_data['Value'], 
                           marker='o', linewidth=2, markersize=4, label=param)
                    
                    # Add target range shading
                    ax.axhspan(target_low, target_high, 
                              color='green', alpha=0.1, label='Target Range')
                    
                    # Add target line
                    ax.axhline(y=target_value, color='green', linestyle='--', alpha=0.7, label='Target')
                    
                    # Formatting with smart unit display and compact spacing
                    ax.set_title(f'{param} ({display_unit})', fontweight='bold', fontsize=12, pad=10)
                    ax.set_ylabel(display_unit, fontsize=10)
                    ax.grid(True, alpha=0.3)
                    ax.legend(loc='upper right', fontsize=9)
                    
                    # Format x-axis with proper spacing
                    ax.tick_params(axis='x', rotation=45, labelsize=9)
                    ax.tick_params(axis='y', labelsize=9)
                    
                    # Ensure good spacing
                    ax.margins(y=0.1)
                    
                else:
                    # No data for this parameter
                    config = self.param_config[param]
                    ax.text(0.5, 0.5, f'No {param} data available', 
                           transform=ax.transAxes, ha='center', va='center',
                           fontsize=11, style='italic')
                    ax.set_title(f'{param} ({config["unit"]})', fontweight='bold', fontsize=12, pad=10)
                    ax.set_ylabel(config["unit"], fontsize=10)
                    ax.grid(True, alpha=0.3)
            
            # Embed in tkinter with proper sizing
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            
            # Pack with proper padding
            chart_widget = canvas.get_tk_widget()
            chart_widget.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Update scroll region after adding charts and focus for mouse wheel
            self.chart_frame.update_idletasks()
            if "Trends" in self.tab_canvases:
                trends_canvas = self.tab_canvases["Trends"]
                trends_canvas.configure(scrollregion=trends_canvas.bbox("all"))
                
                # Ensure canvas can receive focus for mouse wheel scrolling
                trends_canvas.focus_set()
                
                # Bind mouse wheel to the chart widget too
                def _on_chart_wheel(event):
                    trends_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
                chart_widget.bind("<MouseWheel>", _on_chart_wheel)
                chart_widget.bind("<Button-4>", lambda e: trends_canvas.yview_scroll(-1, "units"))
                chart_widget.bind("<Button-5>", lambda e: trends_canvas.yview_scroll(1, "units"))
            
        except Exception as e:
            error_label = tk.Label(self.chart_frame, 
                                 text=f"Error generating graphs:\n{str(e)}", 
                                 font=('Arial', 10), fg='red')
            error_label.pack(pady=50)

    def refresh_history_display(self):
        """Refresh the history table display"""
        # Clear existing items
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        if not os.path.exists(self.db_path):
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all log entries
            rows = cursor.execute('''
                SELECT id, timestamp, parameter, value 
                FROM logs 
                ORDER BY timestamp DESC
            ''').fetchall()
            
            # Insert into treeview
            for row in rows:
                # Format the display values
                row_id, timestamp, parameter, value = row
                formatted_value = f"{value:.3f}" if value < 1 else f"{value:.2f}"
                
                self.history_tree.insert("", "end", values=(row_id, timestamp, parameter, formatted_value))
            
            conn.close()
            
        except Exception as e:
            print(f"Error refreshing history: {e}")

    def show_context_menu(self, event):
        """Show right-click context menu on history table"""
        # Select the item under the cursor
        item = self.history_tree.identify_row(event.y)
        if item:
            self.history_tree.selection_set(item)
            # Show context menu at cursor position
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def edit_history_entry(self, event=None):
        """Edit selected history entry with popup dialog"""
        selection = self.history_tree.selection()
        if not selection:
            if event:  # Called from double-click
                messagebox.showwarning("No Selection", "Please select a row to edit.")
            return
        
        # Get the selected item's data
        item_values = self.history_tree.item(selection[0])['values']
        if not item_values:
            return
            
        row_id, timestamp, parameter, value = item_values
        
        # Create edit dialog
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("Edit Test Entry")
        edit_dialog.geometry("400x300")
        edit_dialog.resizable(False, False)
        
        # Center the dialog
        edit_dialog.transient(self.root)
        edit_dialog.grab_set()
        
        # Edit form
        tk.Label(edit_dialog, text="Edit Test Entry", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Timestamp
        tk.Label(edit_dialog, text="Date & Time:").pack(anchor="w", padx=20)
        timestamp_var = tk.StringVar(value=timestamp)
        tk.Entry(edit_dialog, textvariable=timestamp_var, width=30).pack(pady=5, padx=20, fill="x")
        
        # Parameter
        tk.Label(edit_dialog, text="Parameter:").pack(anchor="w", padx=20, pady=(10,0))
        parameter_var = tk.StringVar(value=parameter.split(" (")[0])  # Remove unit suffix if present
        param_combo = ttk.Combobox(edit_dialog, textvariable=parameter_var, 
                                  values=list(self.param_config.keys()), state="readonly")
        param_combo.pack(pady=5, padx=20, fill="x")
        
        # Value
        tk.Label(edit_dialog, text="Value:").pack(anchor="w", padx=20, pady=(10,0))
        value_var = tk.StringVar(value=str(value))
        tk.Entry(edit_dialog, textvariable=value_var, width=30).pack(pady=5, padx=20, fill="x")
        
        # Unit selector for alkalinity
        unit_frame = ttk.Frame(edit_dialog)
        unit_frame.pack(pady=5)
        
        unit_var = tk.StringVar(value="dKH")
        if "ppm" in parameter.lower():
            unit_var.set("ppm")
        
        def toggle_unit_selector(*args):
            if parameter_var.get() == "Alkalinity":
                unit_frame.pack(pady=5)
            else:
                unit_frame.pack_forget()
        
        parameter_var.trace_add("write", toggle_unit_selector)
        
        tk.Label(unit_frame, text="Unit:").pack(side="left")
        ttk.Radiobutton(unit_frame, text="dKH", variable=unit_var, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(unit_frame, text="ppm", variable=unit_var, value="ppm").pack(side="left", padx=5)
        
        toggle_unit_selector()  # Initial call
        
        # Buttons
        button_frame = ttk.Frame(edit_dialog)
        button_frame.pack(pady=20)
        
        def save_changes():
            try:
                # Validate inputs
                new_timestamp = timestamp_var.get().strip()
                new_parameter = parameter_var.get().strip()
                new_value = float(value_var.get())
                
                if not new_timestamp or not new_parameter:
                    messagebox.showerror("Invalid Input", "Please fill all fields.")
                    return
                
                # Add unit suffix for storage
                if new_parameter == "Alkalinity":
                    param_with_unit = f"{new_parameter} ({unit_var.get()})"
                else:
                    unit = self.param_config[new_parameter]["unit"]
                    param_with_unit = f"{new_parameter} ({unit})"
                
                # Update database
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE logs 
                    SET timestamp = ?, parameter = ?, value = ? 
                    WHERE id = ?
                ''', (new_timestamp, param_with_unit, new_value, row_id))
                conn.commit()
                conn.close()
                
                # Refresh display and close dialog
                self.refresh_history_display()
                edit_dialog.destroy()
                messagebox.showinfo("Success", "Entry updated successfully.")
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid numeric value.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not update entry:\n{str(e)}")
        
        tk.Button(button_frame, text="Save Changes", command=save_changes, 
                 bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="Cancel", command=edit_dialog.destroy, 
                 bg="#95a5a6", fg="white").pack(side="left")

    def delete_selected_row(self):
        """Delete selected row from database without confirmation"""
        selection = self.history_tree.selection()
        if not selection:
            return  # Just return silently if no selection
        
        # Get the selected item's data
        item_values = self.history_tree.item(selection[0])['values']
        if not item_values:
            return
        
        try:
            row_id = int(item_values[0])  # ID is in first column
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM logs WHERE id = ?', (row_id,))
            conn.commit()
            conn.close()
            
            # Refresh display - no popup
            self.refresh_history_display()
            
        except Exception as e:
            pass  # Fail silently - no popup
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete row:\n{str(e)}")

    def export_data_to_csv(self):
        """Export all data to CSV file"""
        if not os.path.exists(self.db_path):
            messagebox.showwarning("No Data", "No data to export.")
            return
            
        try:
            from tkinter import filedialog
            
            # Ask user where to save
            filename = filedialog.asksaveasfilename(
                title="Export Data to CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialname=f"reef_data_export_{datetime.now().strftime('%Y%m%d')}.csv"
            )
            
            if not filename:
                return
            
            # Export data
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('''
                SELECT timestamp as "Date & Time", parameter as "Parameter", value as "Value"
                FROM logs 
                ORDER BY timestamp DESC
            ''', conn)
            conn.close()
            
            df.to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export data:\n{str(e)}")

    def init_database(self):
        """Initialize the SQLite database with proper schema"""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create logs table with better column names
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                parameter TEXT NOT NULL,
                value REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = ReeferMadness(root)
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
