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
        self.root.title("🌊 ReeferMadness v0.26.0 - Ocean Edition")
        self.root.geometry("720x650")  # Slightly taller for ocean aesthetic
        self.root.minsize(700, 600)   # Maintain good minimum size
        self.root.configure(bg='#f0f8ff')  # Seafoam blue background
        
        # Set ocean wave as the sole window icon (remove Python feather)
        try:
            # Try to set a simple ocean wave icon if available, otherwise use emoji
            self.root.iconphoto(False, tk.PhotoImage(data=""))  # Remove default icon
            self.root.wm_iconname("🌊 ReeferMadness")  # Ocean wave for taskbar
        except:
            # Fallback to just title without icon
            pass
        
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

        # Ocean Aesthetic Styling Configuration
        self.setup_ocean_theme()
        
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
        
        # Create scrollable frames for each tab with improved scroll behavior
        self.tabs = {}
        self.tab_canvases = {}
        self.tab_scrollbars = {}
        self.tab_frames = {}
        
        for name in ["Action Plan", "Maintenance", "Trends", "History"]:
            # Create the main tab frame with ocean background
            main_frame = ttk.Frame(self.notebook)
            main_frame.configure(style='Ocean.TFrame')  # Custom ocean style
            
            # Create canvas with ocean background - no gray areas
            canvas = tk.Canvas(main_frame, 
                             borderwidth=0, 
                             highlightthickness=0,
                             bg=self.colors['seafoam_blue'])  # Explicit ocean background
            scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview, width=20)
            
            # Scrollable frame with explicit ocean background
            scrollable_frame = ttk.Frame(canvas)
            scrollable_frame.configure(style='Ocean.TFrame')  # Ocean themed frame
            
            # Configure scrolling
            scrollable_frame.bind(
                "<Configure>",
                lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Store canvas reference for global scrolling
            self.tab_canvases[name] = canvas
            
            # Pack canvas and scrollbar
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Store references
            self.tabs[name] = scrollable_frame  # This is what build functions will use
            self.tab_scrollbars[name] = scrollbar
            self.tab_frames[name] = main_frame
            
            # Add to notebook
            self.notebook.add(main_frame, text=f" {name} ")
        
        self.notebook.pack(expand=True, fill="both")
        
        # Enhanced scroll behavior for nested scrollable widgets
        self.setup_enhanced_scroll_behavior()
        
        # Global scroll binding - redirect all scroll events to active tab canvas
        def global_scroll_handler(event):
            try:
                # Get current active tab
                current_tab = self.notebook.tab(self.notebook.select(), "text").strip()
                if current_tab in self.tab_canvases:
                    canvas = self.tab_canvases[current_tab]
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                    return "break"  # Prevent further propagation
            except:
                pass
        
        # Bind global scroll to root window
        self.root.bind_all('<MouseWheel>', global_scroll_handler)
        self.root.bind_all('<Button-4>', lambda e: global_scroll_handler(type('MockEvent', (), {'delta': 120})()))
        self.root.bind_all('<Button-5>', lambda e: global_scroll_handler(type('MockEvent', (), {'delta': -120})()))

        # Build all tabs
        self.build_action_plan()
        self.build_maintenance()
        self.build_trends()
        self.build_history()
        
        # Unbind mouse wheel from all comboboxes to prevent accidental parameter changes
        self.unbind_combobox_scroll()
        
        # Apply nuclear ocean theme to eliminate any remaining gray widgets
        self.apply_nuclear_ocean_theme()
        
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
        
        # Set window constraints to prevent expanding beyond content
        self.set_window_constraints()
        
        # Set up clean exit handling to prevent zombie processes
        self.setup_clean_exit()
    
    def setup_clean_exit(self):
        """Set up comprehensive exit handling to prevent zombie processes and ensure stability"""
        def on_closing():
            """Handle application closing with complete resource cleanup and thread termination"""
            try:
                print("🌊 Initiating ocean-clean exit sequence...")
                
                # 1. Stop all timers and cancel scheduled tasks
                try:
                    if hasattr(self, 'timer_after_id') and self.timer_after_id:
                        self.root.after_cancel(self.timer_after_id)
                        self.timer_after_id = None
                    print("✅ Timers and scheduled tasks canceled")
                except:
                    pass
                
                # 2. Close all Matplotlib figures to prevent memory leaks
                try:
                    import matplotlib.pyplot as plt
                    plt.close('all')
                    print("✅ Matplotlib figures closed")
                except:
                    pass
                
                # 3. Explicitly close all database connections with force
                try:
                    if hasattr(self, 'db_path') and os.path.exists(self.db_path):
                        # Close any open connections
                        self.close_all_db_connections()
                        
                        # Force close any lingering SQLite connections
                        import gc
                        for obj in gc.get_objects():
                            if isinstance(obj, sqlite3.Connection):
                                try:
                                    obj.close()
                                except:
                                    pass
                    print("✅ Database connections forcefully closed")
                except Exception as e:
                    print(f"Database cleanup warning: {e}")
                
                # 4. Terminate any background threads
                try:
                    import threading
                    active_threads = threading.active_count()
                    if active_threads > 1:  # Main thread + others
                        print(f"⚠️ {active_threads} threads active, forcing cleanup")
                        # Note: We don't forcefully kill threads as it's not safe
                        # The sys.exit() will handle them
                    print("✅ Thread cleanup initiated")
                except:
                    pass
                
                # 5. Force garbage collection to clean up resources
                try:
                    import gc
                    collected = gc.collect()
                    print(f"✅ Garbage collection completed ({collected} objects collected)")
                except:
                    pass
                
                # 6. Destroy tkinter widgets and quit main loop
                try:
                    self.root.quit()     # Exit the main loop
                    self.root.destroy()  # Destroy all widgets
                    print("✅ Tkinter resources destroyed")
                except:
                    pass
                
                print("🌊 Ocean-clean exit sequence completed successfully")
                
                # 7. Force system exit to prevent any zombie processes
                try:
                    import sys
                    import os
                    print("🌊 Forcing system exit to prevent zombies...")
                    os._exit(0)  # Force exit without cleanup (we already did cleanup)
                except:
                    # Final fallback
                    import sys
                    sys.exit(0)
                    
            except Exception as e:
                print(f"💥 Error during cleanup: {e}")
                # Force exit even if cleanup fails
                try:
                    import os
                    os._exit(1)
                except:
                    import sys
                    sys.exit(1)
        
        # Set the window close protocol
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        print("🌊 Enhanced clean exit handler with zombie prevention registered")
    
    def set_window_constraints(self):
        """Set window size constraints based on content to prevent empty space expansion"""
        try:
            # Update all widgets to calculate proper dimensions
            self.root.update_idletasks()
            
            # Get required dimensions (add some padding for safety)
            req_width = self.root.winfo_reqwidth() + 50
            req_height = self.root.winfo_reqheight() + 50
            
            # Set maximum size to prevent expanding beyond content
            # Still allow shrinking for smaller screens
            max_width = max(req_width, 800)  # Minimum reasonable width
            max_height = max(req_height, 700)  # Minimum reasonable height
            
            self.root.maxsize(max_width, max_height)
            
            # Also set a reasonable minimum size
            self.root.minsize(700, 600)
            
        except Exception as e:
            # If constraint setting fails, continue normally
            print(f"Window constraint setting failed: {e}")
            pass

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
        """Save tank volume to preferences file only when manually entered by user"""
        try:
            volume_str = self.tank_volume.get().strip()
            if volume_str and volume_str != "" and volume_str != "0":  # Only save if not empty and not default 0
                volume_float = float(volume_str)
                if volume_float > 0:  # Only save positive numbers
                    prefs_file = os.path.join(os.path.expanduser("~/Documents/ReeferMadness"), "preferences.txt")
                    os.makedirs(os.path.dirname(prefs_file), exist_ok=True)
                    
                    with open(prefs_file, 'w') as f:
                        f.write(volume_str)
                    print(f"✅ Tank volume saved: {volume_str}")
        except (ValueError, IOError) as e:
            print(f"Could not save tank volume: {e}")

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

    def apply_nuclear_ocean_theme(self):
        """Nuclear Option: Recursively force ocean theme on ALL widgets to eliminate gray patchwork"""
        def recursive_ocean_styling(widget):
            try:
                widget_class = widget.winfo_class()
                widget_type = type(widget).__name__
                
                # Skip buttons and input fields (they have their own styling)
                skip_widgets = ['Button', 'Entry', 'Text', 'Scrollbar', 'Scale', 'Spinbox']
                
                if widget_class not in skip_widgets and widget_type not in skip_widgets:
                    # Force ocean background on labels, frames, checkbuttons, radiobuttons
                    if hasattr(widget, 'configure'):
                        try:
                            if widget_class in ['Label', 'Frame', 'Checkbutton', 'Radiobutton', 'LabelFrame']:
                                widget.configure(bg=self.colors['seafoam_blue'])
                                
                                # Also set foreground for text widgets
                                if widget_class in ['Label', 'Checkbutton', 'Radiobutton']:
                                    widget.configure(fg=self.colors['deep_ocean_blue'])
                                    
                                print(f"🌊 Forced ocean theme on {widget_class}: {widget_type}")
                        except tk.TclError:
                            # Some widgets might not support bg/fg options
                            pass
                
                # Recursively apply to all children
                for child in widget.winfo_children():
                    recursive_ocean_styling(child)
                    
            except Exception as e:
                # Continue even if some widget fails
                pass
        
        # Apply to entire application starting from root
        recursive_ocean_styling(self.root)
        print("🌊 Nuclear ocean theme applied to all widgets")

    def setup_ocean_theme(self):
        """Configure ocean-inspired aesthetic with comprehensive color sync and wave-style headers"""
        # Ocean Color Palette
        self.colors = {
            'seafoam_blue': '#f0f8ff',      # Light seafoam background
            'deep_navy': '#1e3d59',         # Deep navy headers
            'deep_ocean_blue': '#1e3d59',   # Deep ocean blue for headers
            'cloud_white': '#ffffff',       # Pure white text
            'ocean_blue': '#2980b9',        # Ocean blue accents
            'coral_orange': '#e74c3c',      # Coral red for warnings
            'sea_green': '#27ae60',         # Sea green for success
            'pearl_gray': '#ecf0f1',        # Pearl gray for subtle elements
            'deep_sea': '#0f3460',          # Deep sea for graphs
            'wave_blue': '#3498db',         # Wave blue for interactive elements
            'transparent_blue': '#3498db40', # Semi-transparent blue
            'waterline_blue': '#e6f3ff',    # Slightly darker blue for waterline effects
        }
        
        # Configure main window background - eliminate all gray
        self.root.configure(bg=self.colors['seafoam_blue'])
        
        # Configure ttk styles for complete ocean transformation
        style = ttk.Style()
        
        # Configure notebook (tab container) styling - complete background sync
        style.configure('TNotebook', 
                       background=self.colors['seafoam_blue'],  # Force seafoam blue background
                       borderwidth=0,
                       relief='flat')
        
        # Tab styling with professional contrast and zero gray
        style.configure('TNotebook.Tab',
                       background=self.colors['seafoam_blue'],  # Ocean background for inactive tabs
                       foreground=self.colors['deep_navy'],     # Deep navy text
                       padding=[20, 12],
                       borderwidth=1,
                       relief='flat',
                       focuscolor='none',  # Remove dotted focus outline
                       font=('Arial', 10, 'bold'))
        
        # Professional tab contrast with better text visibility
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['deep_navy']),      # Deep navy for selected
                            ('active', self.colors['coral_orange']),      # Coral hover state
                            ('!selected', self.colors['seafoam_blue'])],   # Seafoam for inactive
                 foreground=[('selected', self.colors['wave_blue']),      # Bright blue text on selected (not white)
                            ('active', self.colors['deep_navy']),         # Deep navy text on coral hover
                            ('!selected', self.colors['deep_navy'])])      # Navy text on inactive
        
        # Ocean frame styling - complete background sync
        style.configure('TFrame',
                       background=self.colors['seafoam_blue'],
                       borderwidth=0,
                       relief='flat')
        
        # Custom Ocean frame style for explicit ocean theming
        style.configure('Ocean.TFrame',
                       background=self.colors['seafoam_blue'],
                       borderwidth=0,
                       relief='flat')
        
        # Wave-style labelframe styling (heavy ocean frame appearance)
        style.configure('TLabelframe',
                       background=self.colors['seafoam_blue'],
                       borderwidth=3,  # Heavy frame look
                       relief='solid',  # Solid border style
                       bordercolor=self.colors['deep_navy'])  # Deep navy borders
        
        style.configure('TLabelframe.Label',
                       background=self.colors['deep_navy'],  # Deep navy header background
                       foreground=self.colors['cloud_white'],  # White text on navy
                       font=('Arial', 11, 'bold'),  # Bold titles
                       padding=[15, 8])  # Generous padding for professional look
        
        # Ocean-themed entry styling
        style.configure('TEntry',
                       fieldbackground=self.colors['cloud_white'],  # White background, not gray
                       borderwidth=1,
                       relief='flat',
                       bordercolor=self.colors['ocean_blue'],
                       font=('Arial', 9))
        
        # Ocean combobox styling
        style.configure('TCombobox',
                       fieldbackground=self.colors['cloud_white'],  # White background
                       borderwidth=1,
                       relief='flat',
                       bordercolor=self.colors['ocean_blue'],
                       arrowcolor=self.colors['deep_ocean_blue'],
                       font=('Arial', 9))
        
        # Ocean radiobutton styling - force ocean background
        style.configure('TRadiobutton',
                       background=self.colors['seafoam_blue'],
                       foreground=self.colors['deep_ocean_blue'],
                       font=('Arial', 9, 'bold'),  # Bolder font
                       focuscolor='none',
                       borderwidth=0)
        
        # Ocean checkbutton styling - force ocean background
        style.configure('TCheckbutton',
                       background=self.colors['seafoam_blue'],
                       foreground=self.colors['deep_ocean_blue'],
                       font=('Arial', 9, 'bold'),  # Bolder font
                       focuscolor='none',
                       borderwidth=0)
        
        # Ocean label styling - force ocean background
        style.configure('TLabel',
                       background=self.colors['seafoam_blue'],
                       foreground=self.colors['deep_ocean_blue'],
                       font=('Arial', 9, 'bold'))  # Bolder font
        
        # Configure all tkinter (not ttk) widgets to use ocean theme
        # This handles tk.Label, tk.Checkbutton, tk.Radiobutton that don't use ttk styles
        self.root.option_add('*Label.background', self.colors['seafoam_blue'])
        self.root.option_add('*Label.foreground', self.colors['deep_ocean_blue'])
        self.root.option_add('*Checkbutton.background', self.colors['seafoam_blue'])
        self.root.option_add('*Checkbutton.foreground', self.colors['deep_ocean_blue'])
        self.root.option_add('*Radiobutton.background', self.colors['seafoam_blue'])
        self.root.option_add('*Radiobutton.foreground', self.colors['deep_ocean_blue'])
        self.root.option_add('*Frame.background', self.colors['seafoam_blue'])
        
        print("🌊 Complete ocean theme with comprehensive widget styling configured")

    def create_wave_header_frame(self, parent, title_text, padding=15):
        """Create wave-style header frame with waterline effect and floating appearance"""
        # Main container with extra padding for floating bubble effect
        container = ttk.LabelFrame(parent, text=f" {title_text} ", padding=padding)
        container.configure(style='TLabelframe')
        container.pack(fill="x", padx=25, pady=12)  # Increased margins for floating effect
        
        # Add waterline separator effect below header (inside the frame)
        waterline = tk.Frame(container, height=2, bg=self.colors['waterline_blue'])
        waterline.pack(fill="x", pady=(0, 10))  # Space below the waterline
        
        return container

    def create_ocean_button(self, parent, text, command, bg_color=None, width=None):
        """Create ocean-themed button with modern styling"""
        if bg_color is None:
            bg_color = self.colors['ocean_blue']
            
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=self.colors['cloud_white'],
            font=('Arial', 9, 'bold'),
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            activebackground=self.colors['wave_blue'],
            activeforeground=self.colors['cloud_white']
        )
        
        if width:
            button.configure(width=width)
            
        # Add hover effects
        def on_enter(e):
            button.configure(bg=self.colors['wave_blue'])
        
        def on_leave(e):
            button.configure(bg=bg_color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button

    def setup_enhanced_scroll_behavior(self):
        """Setup enhanced scroll behavior for nested scrollable widgets"""
        def create_smart_scroll_handler(canvas, scrollable_widget):
            """Create a smart scroll handler that prioritizes widget scrolling"""
            def smart_scroll(event):
                # Check if the scrollable widget can still scroll in the requested direction
                try:
                    if hasattr(scrollable_widget, 'yview'):
                        top, bottom = scrollable_widget.yview()
                        
                        # Determine scroll direction
                        scroll_up = event.delta > 0 if hasattr(event, 'delta') else event.num == 4
                        
                        if scroll_up and top > 0:
                            # Widget can scroll up, let it handle the event
                            scrollable_widget.yview_scroll(-1, "units")
                            return "break"
                        elif not scroll_up and bottom < 1:
                            # Widget can scroll down, let it handle the event  
                            scrollable_widget.yview_scroll(1, "units")
                            return "break"
                        else:
                            # Widget is at limit, let main canvas handle scrolling
                            if hasattr(event, 'delta'):
                                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                            else:
                                if event.num == 4:
                                    canvas.yview_scroll(-1, "units")
                                elif event.num == 5:
                                    canvas.yview_scroll(1, "units")
                            return "break"
                except:
                    # Fallback to main canvas scrolling
                    try:
                        if hasattr(event, 'delta'):
                            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                        else:
                            if event.num == 4:
                                canvas.yview_scroll(-1, "units")
                            elif event.num == 5:
                                canvas.yview_scroll(1, "units")
                    except:
                        pass
                
                return "break"
            
            return smart_scroll
        
        # Apply enhanced scrolling to text widgets when they're created
        self.enhanced_scroll_widgets = []
        
        # Configure global Toplevel window styling
        self.configure_toplevel_ocean_theme()
        
        print("🌊 Enhanced scroll behavior configured")

    def configure_toplevel_ocean_theme(self):
        """Configure ocean theme for all Toplevel windows and dialogs"""
        # Configure default Toplevel window styling
        self.root.option_add('*Dialog.background', self.colors['seafoam_blue'])
        self.root.option_add('*Dialog.foreground', self.colors['deep_navy'])
        self.root.option_add('*Toplevel.background', self.colors['seafoam_blue'])
        
        # Configure messagebox styling (if possible)
        try:
            # This may not work on all systems, but worth trying
            self.root.tk.call('tk', 'messageBox', '-parent', self.root, '-background', self.colors['seafoam_blue'])
        except:
            pass  # Ignore if not supported
        
        print("🌊 Toplevel ocean theme configured")

    def apply_enhanced_scroll_to_text_widget(self, text_widget):
        """Apply enhanced scroll behavior to text widgets to prevent jarring simultaneous scrolling"""
        def enhanced_text_scroll(event):
            try:
                # Get the current view of the text widget
                top, bottom = text_widget.yview()
                
                # Determine scroll direction
                if hasattr(event, 'delta'):
                    scroll_up = event.delta > 0
                    scroll_amount = int(-1 * (event.delta / 120))
                else:
                    scroll_up = event.num == 4
                    scroll_amount = -1 if scroll_up else 1
                
                # Check if text widget can scroll in requested direction
                if scroll_up and top > 0:
                    # Text widget can scroll up
                    text_widget.yview_scroll(-1, "units")
                    return "break"
                elif not scroll_up and bottom < 1:
                    # Text widget can scroll down  
                    text_widget.yview_scroll(1, "units")
                    return "break"
                else:
                    # Text widget is at limit, let the main app scroll
                    # Find the current tab canvas
                    current_tab = self.notebook.tab(self.notebook.select(), "text").strip()
                    if current_tab in self.tab_canvases:
                        canvas = self.tab_canvases[current_tab]
                        canvas.yview_scroll(scroll_amount, "units")
                    return "break"
                    
            except Exception as e:
                print(f"Enhanced scroll error: {e}")
                return "break"
        
        # Bind the enhanced scroll handler
        text_widget.bind("<MouseWheel>", enhanced_text_scroll, "+")
        text_widget.bind("<Button-4>", enhanced_text_scroll, "+")
        text_widget.bind("<Button-5>", enhanced_text_scroll, "+")
        
        print(f"🌊 Enhanced scroll applied to text widget")

    def apply_enhanced_scroll_to_widget(self, widget, canvas):
        """Apply enhanced scroll behavior to a specific widget"""
        try:
            smart_handler = self.setup_enhanced_scroll_behavior()
            
            # Bind enhanced scroll events
            widget.bind("<MouseWheel>", lambda e: smart_handler(e, canvas, widget), "+")
            widget.bind("<Button-4>", lambda e: smart_handler(e, canvas, widget), "+")  
            widget.bind("<Button-5>", lambda e: smart_handler(e, canvas, widget), "+")
            
            self.enhanced_scroll_widgets.append(widget)
            print(f"🌊 Enhanced scroll applied to {type(widget).__name__}")
        except Exception as e:
            print(f"⚠️ Could not apply enhanced scroll to widget: {e}")

    def unbind_combobox_scroll(self):
        """Unbind mouse wheel from all comboboxes to prevent accidental parameter changes while scrolling"""
        def unbind_widget_recursively(widget):
            try:
                if isinstance(widget, ttk.Combobox):
                    # Unbind mouse wheel events from comboboxes
                    widget.unbind("<MouseWheel>")
                    widget.unbind("<Button-4>") 
                    widget.unbind("<Button-5>")
                    # Also prevent focus-based scrolling
                    widget.bind("<MouseWheel>", lambda e: "break")
                    widget.bind("<Button-4>", lambda e: "break")
                    widget.bind("<Button-5>", lambda e: "break")
                    
                # Recursively check children
                for child in widget.winfo_children():
                    unbind_widget_recursively(child)
            except:
                pass  # Some widgets might not support these operations
        
        # Apply to all tabs
        for tab_frame in self.tabs.values():
            unbind_widget_recursively(tab_frame)

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
        
        # Always update target value for all parameters (including Alkalinity)
        self.target_value.set(str(self.param_config[param]["target"]))
        
        # Show alkalinity unit selector only for alkalinity
        if param == "Alkalinity":
            self.alk_unit_frame.pack(side="left")
        else:
            self.alk_unit_frame.pack_forget()

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
        """Build the Action Plan tab with wave-style headers and floating appearance"""
        frame = self.tabs["Action Plan"]
        
        # Unified Dosing Parameters & Safety Calculator section
        unified_frame = self.create_wave_header_frame(frame, "Dosing Parameters & Safety Calculator")
        
        # Tank Configuration Row
        tank_row = ttk.Frame(unified_frame)
        tank_row.configure(style='Ocean.TFrame')
        tank_row.pack(fill="x", pady=5)
        
        tk.Label(tank_row, text="Tank Volume:", font=('Arial', 9, 'bold'), 
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left")
        volume_entry = tk.Entry(tank_row, textvariable=self.tank_volume, width=8,
                               bg=self.colors['cloud_white'], fg=self.colors['deep_ocean_blue'])
        volume_entry.pack(side="left", padx=5)
        
        ttk.Radiobutton(tank_row, text="Gallons", variable=self.volume_unit, value="Gallons").pack(side="left", padx=5)
        ttk.Radiobutton(tank_row, text="Liters", variable=self.volume_unit, value="Liters").pack(side="left")

        # Product Selection Row
        product_row = ttk.Frame(unified_frame)
        product_row.configure(style='Ocean.TFrame')
        product_row.pack(fill="x", pady=8)
        
        tk.Label(product_row, text="Parameter:", font=('Arial', 9, 'bold'),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left")
        param_combo = ttk.Combobox(product_row, textvariable=self.selected_parameter, 
                                  values=list(self.param_config.keys()), state="readonly", width=12)
        param_combo.pack(side="left", padx=5)
        
        tk.Label(product_row, text="Brand:", font=('Arial', 9, 'bold'),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left", padx=(20,5))
        self.brand_combo = ttk.Combobox(product_row, textvariable=self.selected_brand, 
                                       state="readonly", width=15)
        self.brand_combo.pack(side="left", padx=5)
        
        # Custom concentration frame (shown when Custom brand selected)
        self.custom_frame = ttk.Frame(product_row)
        self.custom_frame.configure(style='Ocean.TFrame')
        tk.Label(self.custom_frame, text="Concentration:", font=('Arial', 9, 'bold'),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left", padx=(10,5))
        custom_entry = tk.Entry(self.custom_frame, textvariable=self.custom_strength, width=8,
                               bg=self.colors['cloud_white'], fg=self.colors['deep_ocean_blue'])
        custom_entry.pack(side="left")
        self.custom_label = tk.Label(self.custom_frame, text="unit", font=('Arial', 9, 'bold'),
                                    bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue'])
        self.custom_label.pack(side="left", padx=(5,0))

        # Safety Calculator Values Row
        calc_row1 = ttk.Frame(unified_frame)
        calc_row1.configure(style='Ocean.TFrame')
        calc_row1.pack(fill="x", pady=8)
        
        tk.Label(calc_row1, text="Current Value:", font=('Arial', 9, 'bold'),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left")
        current_entry = tk.Entry(calc_row1, textvariable=self.current_value, width=10,
                                bg=self.colors['cloud_white'], fg=self.colors['deep_ocean_blue'])
        current_entry.pack(side="left", padx=5)
        
        tk.Label(calc_row1, text="Target Value:", font=('Arial', 9, 'bold'),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left", padx=(20,5))
        target_entry = tk.Entry(calc_row1, textvariable=self.target_value, width=10,
                               bg=self.colors['cloud_white'], fg=self.colors['deep_ocean_blue'])
        target_entry.pack(side="left", padx=5)
        
        # Alkalinity Units Row (only shown for alkalinity parameter)
        calc_row2 = ttk.Frame(unified_frame)
        calc_row2.configure(style='Ocean.TFrame')
        calc_row2.pack(fill="x", pady=5)
        
        self.alk_unit_frame = ttk.Frame(calc_row2)
        self.alk_unit_frame.configure(style='Ocean.TFrame')
        tk.Label(self.alk_unit_frame, text="Alkalinity Unit:", font=('Arial', 9, 'bold'),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left")
        ttk.Radiobutton(self.alk_unit_frame, text="dKH", variable=self.alkalinity_unit, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(self.alk_unit_frame, text="ppm", variable=self.alkalinity_unit, value="ppm").pack(side="left")

        # Calculate button with ocean styling and floating appearance
        button_frame = ttk.Frame(frame)
        button_frame.configure(style='Ocean.TFrame')
        button_frame.pack(pady=20)
        
        self.create_ocean_button(button_frame, "GENERATE SAFETY PLAN", 
                                 self.calculate_dosing_plan).pack()

        # Results with ocean-themed text widget
        result_frame = ttk.Frame(frame)
        result_frame.configure(style='Ocean.TFrame')
        result_frame.pack(fill="both", expand=True, padx=25, pady=(0,10))
        
        self.result_text = tk.Text(result_frame, height=8, wrap=tk.WORD, font=("Arial", 10),
                                  bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue'],  # Match app background
                                  relief='flat', borderwidth=1, 
                                  highlightbackground=self.colors['ocean_blue'])
        result_scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_scrollbar.set)
        
        # Apply enhanced scroll behavior to this text widget
        self.apply_enhanced_scroll_to_text_widget(self.result_text)
        
        self.result_text.pack(side="left", fill="both", expand=True)
        result_scrollbar.pack(side="right", fill="y")
        
        # Initial message with ocean theme and transparency note
        self.result_text.insert("1.0", "🌊 Enter values above and click 'Generate Safety Plan' to see dosing recommendations with detailed mathematical formulas available.")
        self.result_text.config(state="disabled")  # Make read-only
        
        # Tab Explanation Section - MOVED TO BOTTOM (clean header, no icon)
        help_frame = self.create_wave_header_frame(frame, "How to Use Action Plan")
        
        help_text = ("This tab calculates safe dosing schedules to change your reef parameters. "
                    "Enter your tank volume, select the parameter you want to adjust, "
                    "choose your dosing product, then enter current and target values. "
                    "The safety calculator will create a multi-day dosing plan that prevents shocking your corals.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg=self.colors['deep_ocean_blue'], 
                bg=self.colors['seafoam_blue']).pack(anchor="w")

    def build_maintenance(self):
        """Build the Maintenance tab with consumption tracker and logging"""
        frame = self.tabs["Maintenance"]
        
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

        # Row 4.5: Current Daily Dose field for existing dosing integration
        dose_row = ttk.Frame(cons_frame)
        dose_row.pack(fill="x", pady=5)
        
        tk.Label(dose_row, text="Current Daily Dose:", width=15, anchor="w").pack(side="left")
        self.current_daily_dose = tk.StringVar(value="0")  # Default to 0
        tk.Entry(dose_row, textvariable=self.current_daily_dose, width=10).pack(side="left", padx=5)
        tk.Label(dose_row, text="mL (0 if not currently dosing)", width=25, anchor="w", font=('Arial', 8)).pack(side="left", padx=5)

        # Row 5: Alkalinity units (shown only for alkalinity) and Calculate button
        calc_row = ttk.Frame(cons_frame)
        calc_row.pack(fill="x", pady=10)
        
        self.cons_alk_frame = ttk.Frame(calc_row)
        self.cons_alk_frame.pack(side="left")
        tk.Label(self.cons_alk_frame, text="Units:", width=12, anchor="w").pack(side="left")
        ttk.Radiobutton(self.cons_alk_frame, text="dKH", variable=self.cons_alk_unit, value="dKH").pack(side="left", padx=5)
        ttk.Radiobutton(self.cons_alk_frame, text="ppm", variable=self.cons_alk_unit, value="ppm").pack(side="left", padx=5)

        # Calculate button positioned closer to units (not far right) - ocean styling
        self.create_ocean_button(calc_row, "CALCULATE CONSUMPTION RATE", 
                                 self.calculate_consumption_rate).pack(side="left", padx=20)

        # Inline Calculation Results section for transparency (moved below calculator)
        self.consumption_results_frame = self.create_wave_header_frame(frame, "Calculation Results", 15)
        
        # Results display area with permanently visible math transparency and enhanced scroll
        self.consumption_results_text = tk.Text(self.consumption_results_frame, height=12, wrap=tk.WORD, 
                                               font=("Arial", 9), bg=self.colors['seafoam_blue'],  # Match app background 
                                               fg=self.colors['deep_ocean_blue'], relief='flat', 
                                               borderwidth=1, highlightbackground=self.colors['ocean_blue'])
        self.consumption_results_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Apply enhanced scroll behavior to consumption results text
        self.apply_enhanced_scroll_to_text_widget(self.consumption_results_text)
        
        # Initially hide results frame until calculation is performed
        self.consumption_results_frame.pack_forget()

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
        
        # Save button with ocean theme - positioned left to align with section header
        button_frame = ttk.Frame(log_frame)
        button_frame.pack(fill="x", pady=15)
        
        self.save_button = self.create_ocean_button(button_frame, "💾 SAVE TO LOG", 
                                                   self.save_test_entry, self.colors['sea_green'])
        self.save_button.pack(side="left")  # Left-aligned with section header
        
        # Add traces to daily log variables to reset save button when user types
        for param, var in self.log_variables.items():
            var.trace_add("write", self.reset_save_button_on_input)
        
        # Also trace alkalinity unit changes
        self.log_alk_unit.trace_add("write", self.reset_save_button_on_input)
        
        # Tab Explanation Section - MOVED TO BOTTOM (clean header, no icon)
        help_frame = self.create_wave_header_frame(frame, "How to Use Maintenance")
        
        help_text = ("Track your reef's consumption rates and log daily test results. "
                    "The consumption calculator helps you understand how much your tank uses each day "
                    "by comparing start/end values over time. The daily test log keeps a record of "
                    "all your measurements for trend analysis.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg="#2c3e50").pack(anchor="w")

    def build_trends(self):
        """Build the Trends tab with centered title and button layout"""
        frame = self.tabs["Trends"]
        
        # Centered header section at top
        header_frame = ttk.Frame(frame)
        header_frame.configure(style='Ocean.TFrame')
        header_frame.pack(fill="x", pady=(20, 10))
        
        # Reef Parameters title - centered above button
        tk.Label(header_frame, text="Reef Parameter Trends", font=("Arial", 14, "bold"),
                fg=self.colors['deep_navy'], bg=self.colors['seafoam_blue']).pack()
        
        # Refresh button - centered below title
        self.create_ocean_button(header_frame, "REFRESH GRAPHS", self.draw_parameter_graphs, 
                                 self.colors['wave_blue']).pack(pady=(10, 0))
        
        # Chart container (no individual scrolling - let tab handle it)
        self.chart_frame = ttk.Frame(frame)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Tab Explanation Section - MOVED TO BOTTOM (clean header, no icon)
        help_frame = self.create_wave_header_frame(frame, "How to Use Trends")
        
        help_text = ("View your reef parameter trends over time with professional charts. "
                    "The green shaded area shows the safe range for each parameter, while the green dashed line "
                    "shows your optimal target level. You can customize these target lines using the Custom Optimal Levels "
                    "section below the charts. Data points show your actual test results - the goal is to keep your "
                    "parameters within the green safe zones for optimal coral health.")
        
        tk.Label(help_frame, text=help_text, font=("Arial", 9), 
                justify="left", wraplength=520, fg=self.colors['deep_ocean_blue'], 
                bg=self.colors['seafoam_blue']).pack(anchor="w")

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
        
        # Test Timer header with ocean theme
        tk.Label(timer_frame, text="Test Timer:", font=("Arial", 9),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack()
        
        # Timer display with ocean theme background
        self.timer_label = tk.Label(timer_frame, text="00:00", font=("Arial", 18, "bold"), 
                                   fg="#e67e22", cursor="hand2", relief="ridge", bd=2, padx=10, pady=5,
                                   bg=self.colors['seafoam_blue'])  # Ocean background for timer
        self.timer_label.pack()
        self.timer_label.bind("<Button-1>", self.cancel_timer)
        
        # Timer instruction with ocean theme
        tk.Label(timer_frame, text="Click timer to cancel/reset", font=("Arial", 7), 
                fg="#7f8c8d", bg=self.colors['seafoam_blue']).pack()  # Ocean background

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
        
        # Configure tree colors using proper ttk styling approach
        try:
            # Create a custom style for the treeview
            style = ttk.Style()
            style.configure('Ocean.Treeview',
                           background=self.colors['seafoam_blue'],
                           fieldbackground=self.colors['seafoam_blue'],
                           foreground=self.colors['deep_ocean_blue'])
            style.configure('Ocean.Treeview.Heading',
                           background=self.colors['wave_blue'],
                           foreground=self.colors['cloud_white'])
            
            # Apply the custom style
            self.history_tree.configure(style='Ocean.Treeview')
        except Exception as e:
            print(f"⚠️ Could not apply custom treeview styling: {e}")
            # Fallback to default styling if custom fails
        
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
        
        # Control buttons with ocean theme and equal spacing
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        self.create_ocean_button(button_frame, "EXPORT TO CSV", self.export_data_to_csv, 
                                self.colors['ocean_blue']).pack(side="left")
        
        self.create_ocean_button(button_frame, "REFRESH HISTORY", self.refresh_history_display, 
                                self.colors['deep_navy']).pack(side="left", padx=20)  # Equal spacing: 20px
        
        # Clear All Data button with equal spacing and state management
        self.clear_button = self.create_ocean_button(button_frame, "CLEAR ALL DATA", self.clear_all_data_with_confirmation, 
                                                     self.colors['coral_orange'])
        self.clear_button.pack(side="left", padx=20)  # Equal spacing: 20px
        
        # Update clear button state based on data availability
        self.update_clear_button_state()
        
        # Initialize history display
        self.sync_history_kits()
        self.refresh_history_display()
        
        # Database location transparency - show where data is stored
        db_info_frame = ttk.Frame(frame)
        db_info_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        db_location_text = f"📁 Data stored in: {self.db_path}"
        tk.Label(db_info_frame, text=db_location_text, font=("Arial", 8), 
                fg="#7f8c8d", bg="#f0f8ff", anchor="w").pack(anchor="w")
        
        # Tab Explanation Section - MOVED TO BOTTOM (clean header, no icon)
        help_frame = self.create_wave_header_frame(frame, "How to Use History")
        
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
        """Draw the dynamic test kit checklist with clickable labels and strikethrough"""
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
            
            # Interactive step label that can be clicked to toggle checkbox
            step_label = tk.Label(step_frame, text=full_text, 
                                 font=('Arial', 9), wraplength=500, justify="left", anchor="w",
                                 cursor="hand2")  # Hand cursor to indicate clickability
            step_label.pack(side="left", padx=(5,0), fill="x", expand=True, anchor="w")
            
            # Bind click event to label to toggle checkbox
            step_label.bind("<Button-1>", lambda e, idx=i: self.toggle_checkbox_from_label(idx))
            
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
            
            # Add timer button with ocean styling if time period found
            if timer_minutes and timer_minutes > 0:
                timer_btn = tk.Button(step_frame, 
                                    text=f"⏱️ {timer_minutes} MIN TIMER", 
                                    command=lambda m=timer_minutes: self.start_simple_timer(m),
                                    bg="#e67e22", fg="white", 
                                    font=("Arial", 8, "bold"),
                                    relief="flat", bd=0,
                                    cursor="hand2",
                                    activebackground="#d35400")
                timer_btn.pack(side="right", padx=10)

    def toggle_checkbox_from_label(self, step_index):
        """Toggle checkbox when label is clicked"""
        if step_index in self.checkbox_states:
            current_state = self.checkbox_states[step_index].get()
            self.checkbox_states[step_index].set(not current_state)
            self.toggle_step_completion(step_index)

    def toggle_step_completion(self, step_index):
        """Toggle strikethrough when checkbox is clicked or label is clicked"""
        if step_index in self.checkbox_states and step_index in self.step_labels:
            is_checked = self.checkbox_states[step_index].get()
            label = self.step_labels[step_index]
            
            if is_checked:
                # Add strikethrough by changing font - gray when completed
                current_text = label.cget("text")
                label.config(font=('Arial', 9, 'overstrike'), fg="gray")
            else:
                # Remove strikethrough - return to ocean blue default 
                label.config(font=('Arial', 9), fg=self.colors['deep_ocean_blue'])  # Ocean blue default
                
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

    def get_consumption_product_strength(self):
        """Get product strength for consumption calculation"""
        brand = self.cons_brand.get()
        param = self.cons_parameter.get()
        
        if brand == "Custom":
            try:
                return float(self.maint_custom_strength.get())
            except ValueError:
                return 1.0  # Default fallback
        
        return self.param_config[param]["dosing"].get(brand, 1.0)

    def format_consumption_results_with_math(self, details):
        """Format consumption results with permanently visible math formulas (no toggles)"""
        param = details['param']
        tank_vol = details['tank_volume']
        start = details['start_value']
        end = details['end_value']
        depletion = details['depletion']
        days = details['days']
        daily_dep = details['daily_depletion']
        strength = details['product_strength']
        brand = details['brand']
        unit = details['unit']
        base_consumption = details['base_consumption_ml']
        current_dose = details['current_dose']
        final_dose = details['recommended_daily_dose']
        
        result = f"📊 CONSUMPTION ANALYSIS RESULTS\n\n"
        result += f"Parameter: {param} ({unit})\n"
        result += f"Tank Volume: {tank_vol:.1f} gallons\n"
        result += f"Test Period: {days} days\n\n"
        result += f"📈 PARAMETER CHANGE:\n"
        result += f"Start Value: {start} {unit}\n"
        result += f"End Value: {end} {unit}\n"
        result += f"Total Depletion: {depletion:.2f} {unit}\n"
        result += f"Daily Depletion: {daily_dep:.3f} {unit}/day\n\n"
        result += f"🧮 DOSING CALCULATION:\n"
        result += f"Product: {brand}\n"
        result += f"Product Strength: {strength} {unit}/mL\n"
        result += f"Base Consumption Replacement: {base_consumption:.2f} mL/day\n"
        result += f"Current Daily Dose (Existing): {current_dose:.2f} mL/day\n\n"
        result += f"🎯 FINAL RECOMMENDATION:\n"
        result += f"New Daily Dose = {base_consumption:.2f} + {current_dose:.2f} = {final_dose:.2f} mL/day\n\n"
        
        # Add mathematical formulas permanently (clean formatting without icons)
        result += "MATHEMATICAL FORMULAS:\n\n"
        result += "DEPLETION CALCULATION:\n"
        result += f"   Total_Depletion = Start_Value - End_Value\n"
        result += f"   Total_Depletion = {details['start_value']} - {details['end_value']} = {details['depletion']:.2f} {details['unit']}\n\n"
        
        result += "DAILY CONSUMPTION RATE:\n"
        result += f"   Daily_Depletion = Total_Depletion ÷ Days\n"
        result += f"   Daily_Depletion = {details['depletion']:.2f} ÷ {details['days']} = {details['daily_depletion']:.3f} {details['unit']}/day\n\n"
        
        result += "BASE CONSUMPTION REPLACEMENT:\n"
        result += f"   Base_Dose = (Daily_Depletion × Tank_Volume) ÷ Product_Strength\n"
        result += f"   Base_Dose = ({details['daily_depletion']:.3f} × {details['tank_volume']:.1f}) ÷ {details['product_strength']}\n"
        result += f"   Base_Dose = {details['base_consumption_ml']:.2f} mL/day\n\n"
        
        result += "FINAL RECOMMENDATION (WITH EXISTING DOSE):\n"
        result += f"   New_Daily_Dose = Base_Consumption + Current_Daily_Dose\n"
        result += f"   New_Daily_Dose = {details['base_consumption_ml']:.2f} + {details['current_dose']:.2f}\n"
        result += f"   New_Daily_Dose = {details['recommended_daily_dose']:.2f} mL/day\n\n"
        
        result += "VARIABLES USED:\n"
        result += f"   • Tank Volume: {details['tank_volume']:.1f} gallons\n"
        result += f"   • Product: {details['brand']}\n"
        result += f"   • Product Concentration: {details['product_strength']} {details['unit']}/mL\n"
        result += f"   • Test Period: {details['days']} days\n"
        result += f"   • Current Daily Dose: {details['current_dose']:.2f} mL/day\n\n"
        
        result += f"💡 SUMMARY:\n"
        if current_dose > 0:
            result += f"You are currently dosing {current_dose:.2f} mL/day. "
            if final_dose > current_dose:
                increase = final_dose - current_dose
                result += f"Increase to {final_dose:.2f} mL/day (+{increase:.2f} mL)."
            elif final_dose < current_dose:
                decrease = current_dose - final_dose
                result += f"Decrease to {final_dose:.2f} mL/day (-{decrease:.2f} mL)."
            else:
                result += f"Your current dose is perfect! Continue at {final_dose:.2f} mL/day."
        else:
            result += f"Start dosing {final_dose:.2f} mL of {brand} daily to replace natural consumption."
        
        return result

    def toggle_consumption_math(self):
        """Toggle display of consumption calculation math"""
        if not hasattr(self, 'consumption_math_details'):
            return
            
        current_text = self.consumption_results_text.get("1.0", tk.END).strip()
        
        if self.consumption_math_var.get():
            # Show math
            math_text = self.generate_consumption_math_display()
            full_text = current_text + "\n\n" + math_text
        else:
            # Hide math - remove math section
            if "🧮 MATHEMATICAL FORMULAS" in current_text:
                full_text = current_text.split("🧮 MATHEMATICAL FORMULAS")[0].strip()
            else:
                full_text = current_text
        
        self.consumption_results_text.config(state="normal")
        self.consumption_results_text.delete("1.0", tk.END)
        self.consumption_results_text.insert("1.0", full_text)
        self.consumption_results_text.config(state="disabled")

    def generate_consumption_math_display(self):
        """Generate mathematical formulas display for consumption calculation with existing dose integration"""
        details = self.consumption_math_details
        
        math_text = "🧮 MATHEMATICAL FORMULAS:\n\n"
        math_text += "1️⃣ DEPLETION CALCULATION:\n"
        math_text += f"   Total_Depletion = Start_Value - End_Value\n"
        math_text += f"   Total_Depletion = {details['start_value']} - {details['end_value']} = {details['depletion']:.2f} {details['unit']}\n\n"
        
        math_text += "2️⃣ DAILY CONSUMPTION RATE:\n"
        math_text += f"   Daily_Depletion = Total_Depletion ÷ Days\n"
        math_text += f"   Daily_Depletion = {details['depletion']:.2f} ÷ {details['days']} = {details['daily_depletion']:.3f} {details['unit']}/day\n\n"
        
        math_text += "3️⃣ BASE CONSUMPTION REPLACEMENT:\n"
        math_text += f"   Base_Dose = (Daily_Depletion × Tank_Volume) ÷ Product_Strength\n"
        math_text += f"   Base_Dose = ({details['daily_depletion']:.3f} × {details['tank_volume']:.1f}) ÷ {details['product_strength']}\n"
        math_text += f"   Base_Dose = {details['base_consumption_ml']:.2f} mL/day\n\n"
        
        math_text += "4️⃣ FINAL RECOMMENDATION (WITH EXISTING DOSE):\n"
        math_text += f"   New_Daily_Dose = Base_Consumption + Current_Daily_Dose\n"
        math_text += f"   New_Daily_Dose = {details['base_consumption_ml']:.2f} + {details['current_dose']:.2f}\n"
        math_text += f"   New_Daily_Dose = {details['recommended_daily_dose']:.2f} mL/day\n\n"
        
        math_text += "📋 VARIABLES USED:\n"
        math_text += f"   • Tank Volume: {details['tank_volume']:.1f} gallons\n"
        math_text += f"   • Product: {details['brand']}\n"
        math_text += f"   • Product Concentration: {details['product_strength']} {details['unit']}/mL\n"
        math_text += f"   • Test Period: {details['days']} days\n"
        math_text += f"   • Current Daily Dose: {details['current_dose']:.2f} mL/day\n"
        
        return math_text

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
            
            # Real-world alkalinity safety validation based on manufacturer guidelines
            if param == "Alkalinity":
                # Safety limit: 5 mL per 10 gallons per day = 0.5 mL per gallon per day maximum
                max_ml_per_gallon_per_day = 0.5
                max_daily_ml = volume_gallons * max_ml_per_gallon_per_day
                
                # Calculate minimum days needed based on mL dosing limit (more restrictive than dKH limit)
                days_needed_by_ml = max(1, int(abs(total_dose_ml) / max_daily_ml) + 1)
                
                # Also check traditional dKH limit for comparison
                max_daily_change = self.param_config[param]["max_daily"]
                days_needed_by_dkh = max(1, int(abs(difference) / max_daily_change) + 1)
                
                # Use the more conservative (longer) schedule for safety
                days_needed = max(days_needed_by_ml, days_needed_by_dkh, 1)
                
                # Calculate actual daily dose based on conservative schedule
                daily_dose_ml = abs(total_dose_ml) / days_needed
                daily_ml_per_gallon = daily_dose_ml / volume_gallons
                
                # Safety warning if approaching limits
                if daily_ml_per_gallon > 0.4:  # Within 80% of limit
                    safety_warning = f"\n⚠️  APPROACHING SAFETY LIMIT: {daily_ml_per_gallon:.2f} mL/gallon/day (max: 0.5)"
                else:
                    safety_warning = ""
                
                print(f"🔒 Alkalinity Safety Check: {daily_dose_ml:.2f} mL/day ({daily_ml_per_gallon:.2f} mL/gal/day) over {days_needed} days")
                
            else:
                # For other parameters, use existing logic
                max_daily_change = self.param_config[param]["max_daily"]
                days_needed = max(1, int(abs(difference) / max_daily_change) + 1)
                daily_dose_ml = abs(total_dose_ml) / days_needed
                safety_warning = ""
            
            # Store calculation details for math transparency
            self.action_plan_math_details = {
                'param': param,
                'tank_volume': volume_gallons,
                'current': current_val,
                'target': target_val,
                'change_needed': difference,
                'product_strength': strength,
                'brand': self.selected_brand.get(),
                'unit': self.alkalinity_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit'],
                'total_dose': total_dose_ml,
                'max_daily': max_daily_change,
                'daily_dose': daily_dose_ml,
                'days': days_needed
            }
            
            # Format results
            if difference > 0:
                action = "INCREASE"
                dose_direction = "Add"
            else:
                action = "DECREASE" 
                dose_direction = "Reduce by"
                total_dose_ml = abs(total_dose_ml)
                daily_dose_ml = abs(daily_dose_ml)
            
            # Create detailed result message with real-world alkalinity safety validation
            if param == "Alkalinity":
                daily_ml_per_gallon = daily_dose_ml / volume_gallons
                safety_info = f"\n\nREAL-WORLD SAFETY VALIDATION:\n• Daily dose: {daily_dose_ml:.2f} mL = {daily_ml_per_gallon:.2f} mL per gallon\n• Safety limit: 0.5 mL per gallon per day (5 mL per 10 gallons)\n• Your dose is {'SAFE' if daily_ml_per_gallon <= 0.5 else 'EXCEEDS LIMIT'}{safety_warning}"
            else:
                safety_info = ""
                
            result_text = f"""SAFETY DOSING PLAN - {action} {param}

Tank: {volume_gallons:.0f} gallons ({volume_liters:.1f}L)
Change needed: {current_val} → {target_val} {self.alkalinity_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit']}
Product: {self.selected_brand.get()}

RECOMMENDED SCHEDULE:
• Total dose needed: {abs(total_dose_ml):.1f} mL
• {dose_direction}: {daily_dose_ml:.1f} mL per day
• Duration: {days_needed} days
• Test daily and adjust as needed{safety_info}

MATHEMATICAL FORMULAS:

PARAMETER CHANGE REQUIRED:
   Change_Needed = Target_Value - Current_Value
   Change_Needed = {target_val} - {current_val} = {difference:.2f} {self.alkalinity_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit']}

TOTAL DOSE CALCULATION:
   Total_Dose = (Change_Needed * Tank_Volume) / Product_Strength
   Total_Dose = ({difference:.2f} * {volume_gallons:.1f}) / {strength}
   Total_Dose = {abs(total_dose_ml):.2f} mL

DAILY SAFETY DOSING:
   Safety_Limit = 0.5 mL per gallon per day (real-world limit)
   Max_Daily_mL = Tank_Volume * 0.5 = {volume_gallons:.1f} * 0.5 = {volume_gallons * 0.5:.1f} mL/day
   Actual_Daily_Dose = {daily_dose_ml:.2f} mL/day
   Days_Required = Total_Dose / Daily_Dose = {abs(total_dose_ml):.2f} / {daily_dose_ml:.2f} = {days_needed:.1f} days

VARIABLES USED:
   • Tank Volume: {volume_gallons:.1f} gallons  
   • Product: {self.selected_brand.get()}
   • Product Concentration: {strength} {self.alkalinity_unit.get() if param == 'Alkalinity' else self.param_config[param]['unit']}/mL"""
            
            if param == "Alkalinity":
                result_text += f"""
   • Real-World Safety Limit: 0.5 mL per gallon per day (5 mL per 10 gallons)
   • Manufacturer Guidance: Each mL raises 2.1 dKH per gallon"""
            
            result_text += """

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

    def toggle_action_math(self):
        """Toggle display of Action Plan calculation math"""
        if not hasattr(self, 'action_plan_math_details'):
            return
            
        current_text = self.result_text.get("1.0", tk.END).strip()
        
        if self.action_math_var.get():
            # Show math
            math_text = self.generate_action_plan_math_display()
            full_text = current_text + "\n\n" + math_text
        else:
            # Hide math - remove math section
            if "🧮 MATHEMATICAL FORMULAS" in current_text:
                full_text = current_text.split("🧮 MATHEMATICAL FORMULAS")[0].strip()
            else:
                full_text = current_text
        
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", full_text)
        self.result_text.config(state="disabled")

    def generate_action_plan_math_display(self):
        """Generate mathematical formulas display for Action Plan calculation"""
        if not hasattr(self, 'action_plan_math_details'):
            return ""
            
        details = self.action_plan_math_details
        
        math_text = "🧮 MATHEMATICAL FORMULAS:\n\n"
        math_text += "1️⃣ PARAMETER CHANGE REQUIRED:\n"
        math_text += f"   Change_Needed = Target_Value - Current_Value\n"
        math_text += f"   Change_Needed = {details['target']} - {details['current']} = {details['change_needed']:.2f} {details['unit']}\n\n"
        
        math_text += "2️⃣ TOTAL DOSE CALCULATION:\n"
        math_text += f"   Total_Dose = (Change_Needed × Tank_Volume) ÷ Product_Strength\n"
        math_text += f"   Total_Dose = ({details['change_needed']:.2f} × {details['tank_volume']:.1f}) ÷ {details['product_strength']}\n"
        math_text += f"   Total_Dose = {details['total_dose']:.2f} mL\n\n"
        
        math_text += "3️⃣ DAILY SAFETY DOSING:\n"
        math_text += f"   Max_Daily_Change = {details['max_daily']} {details['unit']}/day (safety limit)\n"
        math_text += f"   Daily_Dose = (Max_Daily_Change × Tank_Volume) ÷ Product_Strength\n"
        math_text += f"   Daily_Dose = ({details['max_daily']} × {details['tank_volume']:.1f}) ÷ {details['product_strength']}\n"
        math_text += f"   Daily_Dose = {details['daily_dose']:.2f} mL/day\n\n"
        
        math_text += "4️⃣ SCHEDULE CALCULATION:\n"
        math_text += f"   Days_Required = Total_Dose ÷ Daily_Dose\n"
        math_text += f"   Days_Required = {details['total_dose']:.2f} ÷ {details['daily_dose']:.2f} = {details['days']:.1f} days\n\n"
        
        math_text += "📋 VARIABLES USED:\n"
        math_text += f"   • Tank Volume: {details['tank_volume']:.1f} gallons\n"
        math_text += f"   • Product: {details['brand']}\n"
        math_text += f"   • Product Concentration: {details['product_strength']} {details['unit']}/mL\n"
        math_text += f"   • Safety Limit: {details['max_daily']} {details['unit']}/day max change\n"
        
        return math_text

    def calculate_consumption_rate(self):
        """Calculate daily consumption rate with input validation and inline display"""
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
            
            # Get validated inputs including current daily dose
            tank_volume = float(self.tank_volume.get())
            volume_unit = self.volume_unit.get()
            start_value = float(self.cons_start.get())
            end_value = float(self.cons_end.get())
            days = float(self.cons_days.get())
            brand = self.cons_brand.get()
            
            # Get current daily dose (existing dosing offset)
            current_dose = 0
            if self.current_daily_dose.get().strip():
                try:
                    current_dose = float(self.current_daily_dose.get())
                except ValueError:
                    current_dose = 0
            
            # Convert to gallons if needed for calculation
            tank_volume_gallons = tank_volume / self.LITERS_PER_GALLON if volume_unit == "Liters" else tank_volume
            
            # Calculate depletion and daily consumption
            depletion = start_value - end_value  # Parameter loss
            daily_depletion = depletion / days if days > 0 else 0
            
            # Get product concentration
            product_strength = self.get_consumption_product_strength()
            
            # Calculate required daily dose with existing dose offset
            if param == "Alkalinity":
                # Handle alkalinity unit conversion
                unit = self.cons_alk_unit.get()
                if unit == "ppm" and daily_depletion > 50:
                    daily_depletion_dkh = daily_depletion / self.DKH_TO_PPM_FACTOR
                else:
                    daily_depletion_dkh = daily_depletion
                
                # Calculate base consumption replacement
                base_consumption_ml = (daily_depletion_dkh * tank_volume_gallons) / product_strength
                
                # Final recommendation includes existing dose offset
                # New Daily Dose = (Calculated Consumption) + (Current Daily Dose)
                recommended_daily_dose = base_consumption_ml + current_dose
                
                # Store calculation details for math display
                self.consumption_math_details = {
                    'param': param,
                    'tank_volume': tank_volume_gallons,
                    'start_value': start_value,
                    'end_value': end_value,
                    'depletion': depletion,
                    'days': days,
                    'daily_depletion': daily_depletion_dkh,
                    'product_strength': product_strength,
                    'brand': brand,
                    'unit': unit,
                    'base_consumption_ml': base_consumption_ml,
                    'current_dose': current_dose,
                    'recommended_daily_dose': recommended_daily_dose
                }
            else:
                # For other parameters (future expansion)
                base_consumption_ml = (daily_depletion * tank_volume_gallons) / product_strength
                recommended_daily_dose = base_consumption_ml + current_dose
                
                self.consumption_math_details = {
                    'param': param,
                    'tank_volume': tank_volume_gallons,
                    'start_value': start_value,
                    'end_value': end_value,
                    'depletion': depletion,
                    'days': days,
                    'daily_depletion': daily_depletion,
                    'product_strength': product_strength,
                    'brand': brand,
                    'unit': self.param_config[param]['unit'],
                    'base_consumption_ml': base_consumption_ml,
                    'current_dose': current_dose,
                    'recommended_daily_dose': recommended_daily_dose
                }
            
            # Format results for inline display with permanent math visibility
            result_text = self.format_consumption_results_with_math(self.consumption_math_details)
            
            # Display results inline
            self.consumption_results_text.config(state="normal")
            self.consumption_results_text.delete("1.0", tk.END)
            self.consumption_results_text.insert("1.0", result_text)
            self.consumption_results_text.config(state="disabled")
            
            # Show the results frame
            self.consumption_results_frame.pack(fill="x", padx=20, pady=(10,0))
                
        except ValueError as e:
            messagebox.showerror("Calculation Error", f"Invalid input values: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {str(e)}")
            
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

    def reset_save_button_on_input(self, *args):
        """Reset save button when user modifies any input field"""
        if hasattr(self, 'save_button'):
            self.save_button.config(text="💾 SAVE TO LOG", bg=self.colors['sea_green'])

    def save_test_entry(self):
        """Save test results to database with reactive button feedback"""
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
                self.update_clear_button_state()  # Update clear button state
                
                # Change button text to show success (no popup) - Enhanced with ocean colors
                self.save_button.config(text="✅ SAVED", bg="#2ecc71")  # Brighter green for success
                self.root.after(2000, self.reset_save_button)  # Reset after 2 seconds
            else:
                conn.close()
                # Change button text to show warning (no popup) - Ocean themed warning
                self.save_button.config(text="⚠️ NO DATA", bg="#f39c12")
                self.root.after(2000, self.reset_save_button)  # Reset after 2 seconds
                
        except Exception as e:
            # Show error on button instead of popup - Ocean themed error
            self.save_button.config(text="❌ ERROR", bg=self.colors['coral_orange'])
            self.root.after(2000, self.reset_save_button)  # Reset after 2 seconds

    def reset_save_button(self):
        """Reset save button to original ocean themed state"""
        if hasattr(self, 'save_button'):
            self.save_button.config(text="💾 SAVE TO LOG", bg=self.colors['sea_green'])

    def add_custom_optimal_controls(self):
        """Add custom optimal level controls below charts with persistence and smart feedback"""
        # Strong duplicate prevention - check multiple ways
        if hasattr(self, 'custom_optimal_frame'):
            try:
                if self.custom_optimal_frame and self.custom_optimal_frame.winfo_exists():
                    print("🌊 Custom optimal controls already exist, skipping creation")
                    return
            except tk.TclError:
                # Frame was destroyed, we can recreate
                pass
        
        # Also check if any existing custom optimal sections exist in the Trends tab
        trends_children = self.tabs["Trends"].winfo_children()
        for child in trends_children:
            try:
                if hasattr(child, 'winfo_children'):
                    for subchild in child.winfo_children():
                        if hasattr(subchild, 'cget') and 'Custom Optimal Levels' in str(subchild.cget('text')):
                            print("🌊 Found existing custom optimal section, skipping creation")
                            return
            except:
                continue
        
        # Custom Optimal Levels section
        self.custom_optimal_frame = self.create_wave_header_frame(self.tabs["Trends"], "Custom Optimal Levels", 15)
        
        # Instructions
        tk.Label(self.custom_optimal_frame, 
                text="Customize your optimal target lines for each parameter (leave blank to use factory defaults):",
                font=("Arial", 9), fg=self.colors['deep_ocean_blue'], 
                bg=self.colors['seafoam_blue']).pack(anchor="w", pady=(0,10))
        
        # Load existing custom values from database
        self.load_custom_optimal_levels()
        
        # Create custom optimal level inputs for each parameter
        self.custom_optimal_vars = {}
        self.custom_optimal_labels = {}  # Store label references for updates
        
        for param in self.param_config.keys():
            row_frame = ttk.Frame(self.custom_optimal_frame)
            row_frame.configure(style='Ocean.TFrame')
            row_frame.pack(fill="x", pady=3)
            
            # Parameter label
            config = self.param_config[param]
            factory_default = config['target']  # Original factory default
            current_value = self.get_current_custom_level(param)  # User's custom value or factory default
            unit = config['unit']
            
            tk.Label(row_frame, text=f"{param}:", width=15, anchor="w", font=('Arial', 9, 'bold'),
                    bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue']).pack(side="left")
            
            # Custom optimal value entry with smart alkalinity handling
            self.custom_optimal_vars[param] = tk.StringVar()
            
            # Set current custom value if it exists
            if param in self.custom_optimal_values:
                if param == "Alkalinity":
                    # Display in ppm by default for alkalinity
                    display_value = self.custom_optimal_values[param] * ReeferMadness.DKH_TO_PPM_FACTOR
                    self.custom_optimal_vars[param].set(f"{display_value:.0f}")
                else:
                    self.custom_optimal_vars[param].set(str(self.custom_optimal_values[param]))
            
            custom_entry = tk.Entry(row_frame, textvariable=self.custom_optimal_vars[param], width=12,
                                   bg=self.colors['cloud_white'], fg=self.colors['deep_ocean_blue'])
            custom_entry.pack(side="left", padx=5)
            
            # Smart unit detection for alkalinity
            if param == "Alkalinity":
                # Create dynamic label for alkalinity unit switching
                self.alkalinity_custom_unit = tk.StringVar(value="ppm")
                self.alkalinity_custom_label = tk.Label(row_frame, text="ppm", font=('Arial', 9, 'bold'),
                                                        bg=self.colors['seafoam_blue'], fg=self.colors['deep_ocean_blue'])
                self.alkalinity_custom_label.pack(side="left", padx=2)
                
                # Add smart unit switching trace
                self.custom_optimal_vars[param].trace_add("write", self.smart_alkalinity_unit_switch)
            
            # Enhanced status display with current vs factory defaults
            if param == "Alkalinity":
                current_ppm = current_value * ReeferMadness.DKH_TO_PPM_FACTOR
                factory_ppm = factory_default * ReeferMadness.DKH_TO_PPM_FACTOR
                status_text = f"Current: {current_ppm:.0f} | Factory: {factory_ppm:.0f}"
            else:
                status_text = f"Current: {current_value} | Factory: {factory_default}"
            
            self.custom_optimal_labels[param] = tk.Label(row_frame, text=status_text, font=('Arial', 8),
                                                        bg=self.colors['seafoam_blue'], fg="#7f8c8d")
            self.custom_optimal_labels[param].pack(side="left", padx=10)
        
        # Apply button with feedback
        button_frame = ttk.Frame(self.custom_optimal_frame)
        button_frame.configure(style='Ocean.TFrame')
        button_frame.pack(pady=10)
        
        self.apply_levels_button = self.create_ocean_button(button_frame, "APPLY CUSTOM LEVELS", 
                                                           self.apply_custom_optimal_levels_with_feedback, 
                                                           self.colors['wave_blue'])
        self.apply_levels_button.pack()

    def load_custom_optimal_levels(self):
        """Load custom optimal levels from database"""
        self.custom_optimal_values = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create custom_levels table if it doesn't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS custom_levels (
                parameter TEXT PRIMARY KEY,
                value REAL NOT NULL,
                timestamp TEXT NOT NULL
            )''')
            
            # Load existing custom values
            cursor.execute('SELECT parameter, value FROM custom_levels')
            for param, value in cursor.fetchall():
                self.custom_optimal_values[param] = value
                # Update the actual parameter config
                if param in self.param_config:
                    self.param_config[param]['target'] = value
                    
            conn.close()
            print(f"🌊 Loaded {len(self.custom_optimal_values)} custom optimal levels")
            
        except Exception as e:
            print(f"⚠️ Could not load custom levels: {e}")
            self.custom_optimal_values = {}

    def save_custom_optimal_levels(self, custom_values):
        """Save custom optimal levels to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            for param, value in custom_values.items():
                cursor.execute('''INSERT OR REPLACE INTO custom_levels 
                                 (parameter, value, timestamp) VALUES (?, ?, ?)''',
                               (param, value, timestamp))
            
            conn.commit()
            conn.close()
            print(f"🌊 Saved {len(custom_values)} custom optimal levels to database")
            return True
            
        except Exception as e:
            print(f"❌ Could not save custom levels: {e}")
            return False

    def get_current_custom_level(self, param):
        """Get current custom level or factory default"""
        return self.custom_optimal_values.get(param, self.param_config[param]['target'])

    def smart_alkalinity_unit_switch(self, *args):
        """Smart unit switching for alkalinity in custom levels"""
        try:
            alk_value_str = self.custom_optimal_vars["Alkalinity"].get().strip()
            if alk_value_str and hasattr(self, 'alkalinity_custom_label'):
                alk_value = float(alk_value_str)
                
                # Auto-detect and switch unit display
                if alk_value > 50:  # Likely ppm (120-180 range)
                    self.alkalinity_custom_unit.set("ppm")
                    self.alkalinity_custom_label.config(text="ppm")
                    print(f"🌊 Switched to ppm display: {alk_value}")
                elif alk_value <= 20:  # Likely dKH (7-12 range)
                    self.alkalinity_custom_unit.set("dKH")
                    self.alkalinity_custom_label.config(text="dKH")
                    print(f"🌊 Switched to dKH display: {alk_value}")
                    
        except (ValueError, KeyError, AttributeError):
            pass  # Invalid input or components not ready

    def apply_custom_optimal_levels_with_feedback(self):
        """Apply custom optimal levels with database persistence and user feedback"""
        try:
            custom_values = {}
            
            # Update parameter configuration with custom values
            for param, var in self.custom_optimal_vars.items():
                custom_value = var.get().strip()
                if custom_value:
                    try:
                        custom_float = float(custom_value)
                        if custom_float > 0:  # Only accept positive values
                            
                            # Smart alkalinity unit handling with consistency check
                            if param == "Alkalinity":
                                if custom_float > 50:  # Likely ppm (120-180 range)
                                    # Convert ppm to dKH for internal storage (consistency with rest of app)
                                    target_dkh = custom_float / ReeferMadness.DKH_TO_PPM_FACTOR
                                    custom_values[param] = target_dkh
                                    self.param_config[param]['target'] = target_dkh
                                    print(f"✅ Custom alkalinity set: {custom_float} ppm = {target_dkh:.2f} dKH")
                                else:  # Likely dKH (7-12 range)
                                    custom_values[param] = custom_float
                                    self.param_config[param]['target'] = custom_float
                                    print(f"✅ Custom alkalinity set: {custom_float} dKH")
                            else:
                                custom_values[param] = custom_float
                                self.param_config[param]['target'] = custom_float
                                print(f"✅ Custom optimal level set for {param}: {custom_float}")
                                
                    except ValueError:
                        print(f"⚠️ Invalid value for {param}: {custom_value}")
            
            # Save to database for persistence
            if custom_values:
                saved = self.save_custom_optimal_levels(custom_values)
                if saved:
                    # Update stored custom values
                    self.custom_optimal_values.update(custom_values)
                    
                    # Update status labels
                    self.update_custom_level_labels()
                    
                    # Button feedback
                    self.show_apply_button_feedback("LEVELS SAVED!")
                    
                    # Refresh graphs if they exist
                    self.draw_parameter_graphs()
                else:
                    self.show_apply_button_feedback("SAVE FAILED!", "#e74c3c")
            else:
                # No custom values entered
                self.show_apply_button_feedback("NO CHANGES", "#95a5a6")
                
        except Exception as e:
            print(f"❌ Error applying custom levels: {e}")
            self.show_apply_button_feedback("ERROR!", "#e74c3c")

    def show_apply_button_feedback(self, text, color=None):
        """Show visual feedback on the apply button"""
        if not hasattr(self, 'apply_levels_button'):
            return
            
        original_text = "APPLY CUSTOM LEVELS"
        original_color = self.colors['wave_blue']
        feedback_color = color or self.colors['sea_green']
        
        # Change button appearance
        self.apply_levels_button.config(text=text, bg=feedback_color)
        
        # Reset after 2 seconds
        def reset_button():
            if hasattr(self, 'apply_levels_button'):
                self.apply_levels_button.config(text=original_text, bg=original_color)
        
        self.root.after(2000, reset_button)

    def update_custom_level_labels(self):
        """Update the current vs factory labels"""
        for param in self.param_config.keys():
            if param in self.custom_optimal_labels:
                factory_default = self.param_config[param]['target']  # This is now the custom value
                original_default = {  # Original factory defaults
                    "Alkalinity": 8.5,
                    "Calcium": 420,
                    "Magnesium": 1350,
                    "Phosphate": 0.03
                }.get(param, factory_default)
                
                current_value = self.get_current_custom_level(param)
                
                if param == "Alkalinity":
                    current_ppm = current_value * ReeferMadness.DKH_TO_PPM_FACTOR
                    factory_ppm = original_default * ReeferMadness.DKH_TO_PPM_FACTOR
                    status_text = f"Current: {current_ppm:.0f} | Factory: {factory_ppm:.0f}"
                else:
                    status_text = f"Current: {current_value} | Factory: {original_default}"
                
                self.custom_optimal_labels[param].config(text=status_text)

    def apply_custom_optimal_levels(self):
        """Apply user's custom optimal levels with smart alkalinity unit detection"""
        try:
            # Update parameter configuration with custom values
            for param, var in self.custom_optimal_vars.items():
                custom_value = var.get().strip()
                if custom_value:
                    try:
                        custom_float = float(custom_value)
                        if custom_float > 0:  # Only accept positive values
                            
                            # Smart alkalinity unit handling
                            if param == "Alkalinity":
                                if custom_float > 50:  # Likely ppm (120-180 range)
                                    # Convert ppm to dKH for internal storage
                                    target_dkh = custom_float / ReeferMadness.DKH_TO_PPM_FACTOR
                                    self.param_config[param]['target'] = target_dkh
                                    print(f"✅ Custom alkalinity set: {custom_float} ppm = {target_dkh:.2f} dKH")
                                else:  # Likely dKH (7-12 range)
                                    self.param_config[param]['target'] = custom_float
                                    print(f"✅ Custom alkalinity set: {custom_float} dKH")
                            else:
                                self.param_config[param]['target'] = custom_float
                                print(f"✅ Custom optimal level set for {param}: {custom_float}")
                                
                    except ValueError:
                        print(f"⚠️ Invalid value for {param}: {custom_value}")
            
            # Refresh the graphs to show new optimal lines (without creating new controls)
            self.draw_parameter_graphs()
            
        except Exception as e:
            print(f"❌ Error applying custom levels: {e}")

    def draw_parameter_graphs(self):
        """Draw trend graphs that scale to fit window width with proper scrolling"""
        # Clear existing charts
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        if not os.path.exists(self.db_path):
            tk.Label(self.chart_frame, text="No data available. Add some test results first!", 
                    font=('Arial', 12)).pack(pady=50)
            return
        
        # Clear any existing matplotlib figures to prevent ghost title interference
        plt.close('all')  # Close all previous figures
        
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
            
            # Create properly sized subplots that fit the window with ocean theme
            num_params = len(self.param_config)
            min_height_per_chart = 3  # Slightly smaller for better fit
            total_height = min_height_per_chart * num_params
            
            # Configure matplotlib with complete title suppression
            plt.style.use('default')  # Reset any previous styles
            plt.rcParams.update({'figure.titlesize': 0})  # Suppress default title sizing
            
            fig, axes = plt.subplots(num_params, 1, figsize=(chart_width, total_height), 
                                   constrained_layout=True, facecolor='#f0f8ff')  # Seafoam background
            if num_params == 1:
                axes = [axes]  # Make it a list for consistency
            
            # Explicitly clear any figure-level title to prevent ghost text
            fig.suptitle('')  # Empty title to override any matplotlib defaults
            fig._suptitle = None  # Force clear internal title reference
            
            # Additional title suppression for constrained layout
            if hasattr(fig, 'set_constrained_layout_pads'):
                fig.set_constrained_layout_pads(hspace=0.1, wspace=0.1)
            
            # No matplotlib title - using Tkinter label above button for clean UI
            # This prevents duplicate "Reef Parameter Trends" ghost text
            
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
                    
                    # Clean, professional chart styling
                    ax.set_facecolor('#f8fbff')  # Very light blue background for charts
                    
                    # Plot the data with professional ocean aesthetics
                    ax.plot(param_data['Date'], param_data['Value'], 
                           color='#0f3460',  # Deep sea blue line
                           linewidth=3, 
                           markersize=6, 
                           marker='o',
                           markerfacecolor='#2980b9',  # Ocean blue markers
                           markeredgecolor='#1e3d59',  # Deep navy edge
                           markeredgewidth=2,
                           alpha=0.9)
                    
                    # Add target range shading (clear and simple)
                    ax.axhspan(target_low, target_high, 
                              color='#27ae60', alpha=0.15, zorder=0)  # Light green safe zone
                    
                    # Add target line (user can customize this in future)
                    ax.axhline(y=target_value, color='#27ae60', linestyle='--', 
                              linewidth=2, alpha=0.8)  # Green target line
                    
                    # Ocean-themed chart formatting with smaller, centered titles
                    ax.set_title(f'{param} ({display_unit})', 
                                fontweight='bold', fontsize=10, pad=10, color='#1e3d59',  # Reduced from 12 to 10
                                ha='center')  # Explicitly center the title
                    ax.set_ylabel(display_unit, fontsize=9, color='#1e3d59', fontweight='bold')  # Slightly smaller ylabel
                    
                    # Ocean-inspired grid
                    ax.grid(True, alpha=0.3, color='#2980b9', linestyle='-', linewidth=0.5)
                    ax.set_axisbelow(True)  # Grid behind data
                    
                    # Remove confusing legends - information moved to How to Use section
                    # No legend needed as chart purpose is clear from title and data
                    
                    # Ocean-themed tick styling
                    ax.tick_params(axis='x', rotation=45, labelsize=8, colors='#1e3d59')
                    ax.tick_params(axis='y', labelsize=8, colors='#1e3d59')
                    
                    # Ocean color spines
                    for spine in ax.spines.values():
                        spine.set_color('#2980b9')
                        spine.set_linewidth(1.5)
                    
                    # Ensure good spacing with ocean feel
                    ax.margins(y=0.1)
                    
                else:
                    # No data for this parameter - clean empty state
                    config = self.param_config[param]
                    ax.set_facecolor('#f8fbff')  # Light blue background
                    ax.text(0.5, 0.5, f'No {param} data available\nStart logging to see trends!', 
                           transform=ax.transAxes, ha='center', va='center',
                           fontsize=11, style='italic', color='#1e3d59',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='#f0f8ff', alpha=0.8))
                    ax.set_title(f'{param} ({config["unit"]})', 
                                fontweight='bold', fontsize=10, pad=10, color='#1e3d59',  # Reduced size and better centering
                                ha='center')  # Explicitly center
                    ax.set_ylabel(config["unit"], fontsize=9, color='#1e3d59')  # Smaller ylabel
                    ax.grid(True, alpha=0.3, color='#2980b9')
            
            # Embed in tkinter with proper sizing
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            
            # Pack with proper padding
            chart_widget = canvas.get_tk_widget()
            chart_widget.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Add custom optimal level controls below charts
            self.add_custom_optimal_controls()
            
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
        
        # Create edit dialog with ocean theme and proper sizing
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("Edit Test Entry")
        edit_dialog.geometry("400x550")  # Taller to ensure buttons are visible
        edit_dialog.resizable(False, False)
        edit_dialog.configure(bg=self.colors['seafoam_blue'])  # Ocean theme background
        
        # Center the dialog
        edit_dialog.transient(self.root)
        edit_dialog.grab_set()
        
        # Edit form with ocean theme
        tk.Label(edit_dialog, text="Edit Test Entry", font=("Arial", 14, "bold"),
                bg=self.colors['seafoam_blue'], fg=self.colors['deep_navy']).pack(pady=10)
        
        # Timestamp with ocean theme
        tk.Label(edit_dialog, text="Date & Time:", bg=self.colors['seafoam_blue'], 
                fg=self.colors['deep_navy']).pack(anchor="w", padx=20)
        timestamp_var = tk.StringVar(value=timestamp)
        tk.Entry(edit_dialog, textvariable=timestamp_var, width=30,
                bg=self.colors['cloud_white'], fg=self.colors['deep_navy']).pack(pady=5, padx=20, fill="x")
        
        # Parameter with ocean theme
        tk.Label(edit_dialog, text="Parameter:", bg=self.colors['seafoam_blue'], 
                fg=self.colors['deep_navy']).pack(anchor="w", padx=20, pady=(10,0))
        parameter_var = tk.StringVar(value=parameter.split(" (")[0])  # Remove unit suffix if present
        param_combo = ttk.Combobox(edit_dialog, textvariable=parameter_var, 
                                  values=list(self.param_config.keys()), state="readonly")
        param_combo.pack(pady=5, padx=20, fill="x")
        
        # Value with ocean theme
        tk.Label(edit_dialog, text="Value:", bg=self.colors['seafoam_blue'], 
                fg=self.colors['deep_navy']).pack(anchor="w", padx=20, pady=(10,0))
        value_var = tk.StringVar(value=str(value))
        tk.Entry(edit_dialog, textvariable=value_var, width=30,
                bg=self.colors['cloud_white'], fg=self.colors['deep_navy']).pack(pady=5, padx=20, fill="x")
        
        # Unit selector for alkalinity with ocean theme
        unit_frame = ttk.Frame(edit_dialog)
        unit_frame.configure(style='Ocean.TFrame')
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
        
        # Create button frame at bottom with proper padding
        button_frame = ttk.Frame(edit_dialog)
        button_frame.configure(style='Ocean.TFrame')
        button_frame.pack(pady=20, padx=20, fill="x", side="bottom")
        
        # Save Changes button with ocean styling and proper padding to prevent clipping
        save_btn = tk.Button(button_frame, text="Save Changes", command=save_changes,
                            bg=self.colors['sea_green'], fg=self.colors['cloud_white'], 
                            font=("Arial", 10, "bold"), relief='flat', borderwidth=0,
                            cursor='hand2', activebackground=self.colors['wave_blue'],
                            activeforeground=self.colors['cloud_white'],
                            pady=8, ipady=5)  # ipady=5 prevents text clipping
        save_btn.pack(side="left", padx=10)
        
        # Cancel button with ocean styling and proper padding to prevent clipping
        cancel_btn = tk.Button(button_frame, text="Cancel", command=edit_dialog.destroy,
                              bg="#95a5a6", fg=self.colors['cloud_white'], 
                              font=("Arial", 10, "bold"), relief='flat', borderwidth=0,
                              cursor='hand2', activebackground="#7f8c8d",
                              activeforeground=self.colors['cloud_white'],
                              pady=8, ipady=5)  # ipady=5 prevents text clipping
        cancel_btn.pack(side="left")

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

    def clear_all_data_with_confirmation(self):
        """Clear all data with streamlined single confirmation and data validation"""
        from tkinter import messagebox
        
        # Check if there's any data to clear first
        if not self.has_data_to_clear():
            messagebox.showinfo("No Data", "There is no data to clear.")
            return
        
        # Single, clear confirmation dialog with high-contrast warning
        response = messagebox.askyesno(
            "⚠️ PERMANENT DATA DELETION", 
            "🗑️ This will PERMANENTLY DELETE all your reef test data.\n\n"
            "This action cannot be undone!\n\n"
            "• All test history will be lost\n"
            "• All charts will be cleared\n"
            "• Database will be completely wiped\n\n"
            "Are you sure you want to proceed?",
            icon="warning"
        )
        
        if response:  # User clicked Yes
            # Proceed immediately to data deletion (no second popup)
            try:
                success = self.clear_all_data()
                if success:
                    # No success popup - just refresh displays
                    self.refresh_history_display()
                    self.draw_parameter_graphs()
                    self.update_clear_button_state()  # Update button state
                else:
                    messagebox.showerror("Error", "❌ Could not delete all data.\n\nPlease check the database file permissions.")
            except Exception as e:
                messagebox.showerror("Error", f"Database deletion failed: {str(e)}")
        # If No was clicked, do nothing - no additional message needed

    def has_data_to_clear(self):
        """Check if there's any data in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM logs')
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False  # Assume no data if can't check

    def update_clear_button_state(self):
        """Update Clear All Data button state based on data availability"""
        if hasattr(self, 'clear_button'):
            has_data = self.has_data_to_clear()
            if has_data:
                self.clear_button.config(state='normal', bg=self.colors['coral_orange'])
            else:
                self.clear_button.config(state='disabled', bg='#95a5a6')  # Grayed out

    def clear_all_data(self):
        """Actually clear all data - internal method"""
        try:
            print("🗑️ Clearing all test data...")
            
            # Method 1: Try to drop the table (fastest)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS logs')
            cursor.execute('''CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                parameter TEXT NOT NULL,
                value REAL NOT NULL
            )''')
            conn.commit()
            conn.close()
            print("✅ Database table cleared and recreated")
            return True
            
        except Exception as e:
            print(f"⚠️ Method 1 failed: {e}")
            
            # Method 2: Delete the database file
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    print("✅ Database file deleted")
                    
                    # Reinitialize database
                    self.setup_database()
                    print("✅ Database recreated")
                    return True
                    
            except Exception as e2:
                print(f"⚠️ Method 2 failed: {e2}")
                messagebox.showerror(
                    "Error", 
                    "❌ Could not delete all data.\n\n"
                    "Some files may be in use.\n"
                    "Please close the application and manually delete:\n"
                    f"{self.db_path}"
                )
                return False
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('DROP TABLE IF EXISTS logs')
                conn.commit()
                conn.close()
                print("✅ Database table dropped successfully")
                
                # Recreate the empty table
                self.init_database()
                return True
                
            except Exception as e:
                print(f"Table drop failed: {e}, trying file deletion...")
                
                # Method 2: Delete the entire database file
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    print("✅ Database file deleted successfully")
                    
                    # Recreate the database
                    self.init_database()
                    return True
                    
            return False
            
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            return False

    def export_data_to_csv(self):
        """Export all data to CSV file"""
        if not os.path.exists(self.db_path):
            messagebox.showwarning("No Data", "No data to export.")
            return
            
        try:
            from tkinter import filedialog
            
            # Ask user where to save - using correct Tkinter parameters
            filename = filedialog.asksaveasfilename(
                title="Export Data to CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"reef_data_export_{datetime.now().strftime('%Y%m%d')}.csv"  # Fixed: initialfile instead of initialname
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

    def get_db_connection(self):
        """Get database connection with proper resource management"""
        return sqlite3.connect(self.db_path)
    
    def close_all_db_connections(self):
        """Ensure all database connections are properly closed"""
        try:
            # Force close any remaining connections by creating and immediately closing one
            conn = sqlite3.connect(self.db_path)
            conn.close()
            
            # Also try to close any connection that might be lingering
            import gc
            for obj in gc.get_objects():
                if isinstance(obj, sqlite3.Connection):
                    try:
                        obj.close()
                    except:
                        pass
        except Exception as e:
            print(f"Database connection cleanup warning: {e}")

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
    """Main application entry point with proper error handling and cleanup"""
    app = None
    root = None
    
    try:
        print("🚀 Starting ReeferMadness v0.26.0...")
        
        # Initialize Tkinter root
        root = tk.Tk()
        
        # Initialize application
        app = ReeferMadness(root)
        
        # Center the window on screen
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        print("✅ Application initialized successfully")
        
        # Start the main event loop
        root.mainloop()
        
    except KeyboardInterrupt:
        print("🛑 Application interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error during startup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure proper cleanup even if main loop crashes
        print("🧹 Performing final cleanup...")
        try:
            if app:
                # Close any remaining database connections
                app.close_all_db_connections()
                
            # Close any Matplotlib figures
            try:
                import matplotlib.pyplot as plt
                plt.close('all')
            except:
                pass
                
            if root:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass
                    
            print("✅ Cleanup completed")
        except:
            pass
        
        # Force exit to prevent zombie processes
        try:
            import sys
            sys.exit(0)
        except:
            pass


if __name__ == "__main__":
    main()
