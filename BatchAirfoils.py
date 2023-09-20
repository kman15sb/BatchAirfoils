# ToDo
# Need to fix rear airfoil rotation 
#   - When it rotates it rotates around the center of a box made by the extents of the sketch
#   - When it rotates the extents change in x-y axis, so I guess the center changes even tho it does not seem like it should or something idk yet
# Need to add main airfoil rotation 
#   - Need to do math of how to move and rotate rear airfoil based on rotation angle of main airfoil
# Need to add command handling 
#   - make it easier to specify steps and distances/angles
# Import airfoil dats in program
#   - Add the ability to select multiple airfoil files and set their scale, chord length, aoa, and distances from origin

import adsk.core, adsk.fusion, traceback, os, math

xSteps = 2
dx = 5
ySteps = 2
dy = 5 
aoaSecondarySteps = 2
daS=5 # In degrees
aoaMainSteps = 1
dam=10

ui = None
rootComp = None

# Function to project sketch geometry into a target sketch
def projectSketchGeometry(source_sketch, target_sketch):
    # Create a collection for the sketch geometry
    sketch_entities = adsk.core.ObjectCollection.create()

    # Add all sketch geometry to the collection
    for entity in source_sketch.sketchCurves:
        sketch_entities.add(entity)

    # Create a projection operation
    projection = target_sketch.project(sketch_entities)

    return projection
    
def run(context):
    try:
        # Script Setup
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design: adsk.fusion.Design = app.activeProduct
        rootComp = design.rootComponent
        
        # Get list of sketches in the composition
        sketches = rootComp.sketches
        sketch_names = []
        
        for skecth in sketches:
            sketch_names.append(skecth.name)

        # Get the folder to export to from the user
        folderDialog = ui.createFolderDialog()
        folderDialog.title = 'Specify Export Folder'
        results = folderDialog.showDialog()
        if results != adsk.core.DialogResults.DialogOK:
            return

        folder = folderDialog.folder
        
        # rotate main airfoil (currently does nothing)
        for aoaMain in range(aoaMainSteps):
            rear_sketch = rootComp.sketches.itemByName('rear')

            # Calculate the center point for rotation
            sketchExtents = rear_sketch.boundingBox
            
            center_x = (sketchExtents.minPoint.x + sketchExtents.maxPoint.x) / 2
            center_y = (sketchExtents.minPoint.y + sketchExtents.maxPoint.y) / 2
            center_point = adsk.core.Point3D.create(center_x, center_y, 0)

            # Calculate vectors/rotations for dx, dy, rot, and reverse_rot and create transformations 
            y_translation_vector = adsk.core.Vector3D.create(0, dy, 0)
            y_transform = adsk.core.Matrix3D.create()
            y_transform.translation = y_translation_vector
              
            x_translation_vector = adsk.core.Vector3D.create(dx, 0, 0)                
            x_transform = adsk.core.Matrix3D.create()
            x_transform.translation = x_translation_vector    
            
            rot_transform = adsk.core.Matrix3D.create()
            rot_transform.setToRotation(math.radians(daS),rootComp.zConstructionAxis.geometry.getData()[2],center_point)
            
            reverse_rot_transform = adsk.core.Matrix3D.create()
            reverse_rot_transform.setToRotation(-math.radians(aoaSecondarySteps*daS),rootComp.zConstructionAxis.geometry.getData()[2],center_point)
            
            # move rear airfoil on x axis
            for i in range(xSteps):
                   
                # move rear airfoil on y axis
                for j in range(ySteps):
                    
                    # Rotate the rear airfoil by the center
                    for k in range(aoaSecondarySteps):                        
                        
                        # Create a new sketch to combine the others into
                        combined_sketch = rootComp.sketches.add(rootComp.xYConstructionPlane)

                        # Loop through the sketch names and project their geometry into the new sketch
                        for sketch_name in sketch_names:
                            sketch = rootComp.sketches.itemByName(sketch_name)
                            if sketch:
                                projectSketchGeometry(sketch, combined_sketch)
                        
                        # Create a patch with the combined sketch
                        profilecurve = combined_sketch.profiles[0]
                        patches = rootComp.features.patchFeatures
                        patchInput = patches.createInput(profilecurve, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                        patch = patches.add(patchInput)
                        
                        # Export the file as STEP.
                        exportMgr = design.exportManager
                        filename = os.path.join(folder, 'test_{}_{}_{}_{}.step'.format(i,j,k,aoaMain))
                        stepOptions = exportMgr.createSTEPExportOptions(filename, rootComp)
                        exportMgr.execute(stepOptions)
                        
                        # delete temporary sketch and patch
                        combined_sketch.deleteMe()
                        patch.deleteMe()
                        
                        # Rotate rear wing by daS
                        rear_sketch.transform = rot_transform
                    
                    # Return rear airfoil to original rotation orientation                     
                    rear_sketch.transform = reverse_rot_transform
                    
                    # Move rear wing by dy
                    rear_sketch.transform = y_transform  
                
                # Reverse y translations   
                reverse_y_translation_vector = adsk.core.Vector3D.create(0,-(ySteps)*dy,0)
                reverse_y_transform = adsk.core.Matrix3D.create()
                reverse_y_transform.translation = reverse_y_translation_vector
                rear_sketch.transform = reverse_y_transform
                
                # Move rear wing by dx               
                rear_sketch.transform = x_transform  
            
            # Reverse x translations    
            reverse_x_translation_vector = adsk.core.Vector3D.create(-(xSteps)*dx, 0, 0)
            reverse_x_transform = adsk.core.Matrix3D.create()
            reverse_x_transform.translation = reverse_x_translation_vector  
            rear_sketch.transform = reverse_x_transform    
        
        # Update the display
        app.activeViewport.refresh()
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))