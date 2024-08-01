import maya.cmds as cmds

class RigUtils:
    captured_attrs = {}

    def __init__(self):
        self.attributes = [
            # "Neck_3_jnt_parentConstraint1.HeadW0",
            # "Neck_2_jnt_parentConstraint1.Neck1W0",
            # "Neck_2_jnt_parentConstraint1.NeckW1",
            # "Neck_1_jnt_parentConstraint1.Spine3W0",
            "C_head_BLEND.Head",
            "teeth_BLEND.Teeth",
            "L_iris_BLEND.L_iris_GEO",
            "L_lens_BLEND.L_lens_GEO",
            "L_sclera_BLEND.L_sclera_GEO",
            "L_eyeball_BLEND.L_eyeball_GEO",
            "R_iris_BLEND.R_iris_GEO",
            "R_lens_BLEND.R_lens_GEO",
            "R_sclera_BLEND.R_sclera_GEO",
            "R_eyeball_BLEND.R_eyeball_GEO"
        ]
    
    def find_full_name(self, attr_name):
        # Extract the base name without the namespace
        base_name = attr_name.split(":")[-1]
        # Find all matching objects and attributes in the scene
        matching_objects = cmds.ls(f"*:{base_name}")
        if matching_objects:
            return matching_objects[0]
        else:
            return None
    
    @classmethod
    def capture_attrs(cls):
        instance = cls()
        for attr in instance.attributes:
            full_name = instance.find_full_name(attr)
            if full_name:
                try:
                    cls.captured_attrs[attr] = cmds.getAttr(full_name)
                    print(f"Successfully captured attribute {full_name}: {cls.captured_attrs[attr]}")
                except Exception as e:
                    print(f"Error capturing attribute {full_name}: {e}")
            else:
                print(f"Error capturing attribute {attr}: No matching object found")
    
    @classmethod
    def force_attrs(cls):
        instance = cls()
        attribute_values = {
            # "Neck_3_jnt_parentConstraint1.HeadW0": 0,
            # "Neck_2_jnt_parentConstraint1.Neck1W0": 0,
            # "Neck_2_jnt_parentConstraint1.NeckW1": 0,
            # "Neck_1_jnt_parentConstraint1.Spine3W0": 0,
            "C_head_BLEND.Head": 1,
            "teeth_BLEND.Teeth": 1,
            "L_iris_BLEND.L_iris_GEO": 1,
            "L_lens_BLEND.L_lens_GEO": 1,
            "L_sclera_BLEND.L_sclera_GEO": 1,
            "L_eyeball_BLEND.L_eyeball_GEO": 1,
            "R_iris_BLEND.R_iris_GEO": 1,
            "R_lens_BLEND.R_lens_GEO": 1,
            "R_sclera_BLEND.R_sclera_GEO": 1,
            "R_eyeball_BLEND.R_eyeball_GEO": 1
        }
        for attr, value in attribute_values.items():
            full_name = instance.find_full_name(attr)
            if full_name:
                try:
                    cmds.setAttr(full_name, value)
                    print(f"Successfully set attribute {full_name} to {value}")
                except Exception as e:
                    print(f"Error setting attribute {full_name} to {value}: {e}")
            else:
                print(f"Error setting attribute {attr}: No matching object found")
    
    @classmethod
    def restore_attrs(cls):
        instance = cls()
        for attr, value in cls.captured_attrs.items():
            full_name = instance.find_full_name(attr)
            if full_name:
                try:
                    cmds.setAttr(full_name, value)
                    print(f"Successfully restored attribute {full_name} to {value}")
                except Exception as e:
                    print(f"Error restoring attribute {full_name} to {value}: {e}")
            else:
                print(f"Error restoring attribute {attr}: No matching object found")

# Example usage:
# RigUtils.capture_attrs()
# RigUtils.force_attrs()
# RigUtils.restore_attrs()
