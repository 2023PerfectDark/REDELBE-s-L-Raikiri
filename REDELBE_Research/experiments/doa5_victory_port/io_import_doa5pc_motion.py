bl_info = {
    "name": "Import DOA5PC Motion",
    "author": "dtk mnr",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export",
    "description": "Import DOA5PC Motion",
    "warning": "",
    "category": "Import-Export",
}

import bpy
import struct, os, io, array
import math
import mathutils
from mathutils import Vector, Matrix
import binascii
from bpy.props import *
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        path_reference_mode,
        axis_conversion,
        )
from bpy.types import (
        Operator,
        OperatorFileListElement,
        )



prop = {}

set_default_target = True

bonenames = {}
armatures = []
subarmatures = []
cameras = []

bonenames["MOT00_Hips"] = (
    "MOT00_Hips",
    "MOT01_Head",
    "MOT02_Chest",
    "MOT_*Foot.1.L",
    "MOT_*ForeArm.1.L",
    "MOT_*Hand.1.L",
    "MOT_*UpLeg.1.L",
    "MOT_*Leg.1.L",
    "MOT_*Arm.1.L",
    "MOT_*Foot.1.R",
    "MOT_*ForeArm.1.R",
    "MOT_*Hand.1.R",
    "MOT_*UpLeg.1.R",
    "MOT_*Leg.1.R",
    "MOT_*Arm.1.R",
    "MOT15_Neck",
    "MOT16_Waist",
    "MOT_*Shoulder.1.L",
    "MOT_*Toe.1.L",
    "MOT_*Shoulder.1.R",
    "MOT_*Toe.1.R"
)

bonenames["OPT_Face_Root"] = (
    "OPT_Face_c_eyebrow",
    "OPT_Face_c_lip_lower",
    "OPT_Face_c_lip_upper",
    "OPT_Face_c_nose",
    "OPT_Face_c_tongue_a",
    "OPT_Face_c_tongue_b",
    "OPT_Face_jaw",
    "OPT_Face_*_cheek_a.0.l",
    "OPT_Face_*_cheek_b.0.l",
    "OPT_Face_*_cheek_c.0.l",
    "OPT_Face_*_eye.0.l",
    "OPT_Face_*_eye_lower_a.0.l",
    "OPT_Face_*_eye_lower_b.0.l",
    "OPT_Face_*_eyebrow_a.0.l",
    "OPT_Face_*_eyebrow_b.0.l",
    "OPT_Face_*_eyebrow_c.0.l",
    "OPT_Face_*_eyelid.0.l",
    "OPT_Face_*_forehead.0.l",
    "OPT_Face_*_lip_lower.0.l",
    "OPT_Face_*_lip_outside.0.l",
    "OPT_Face_*_lip_upper.0.l",
    "OPT_Face_*_nose_a.0.l",
    "OPT_Face_*_nose_b.0.l",
    "OPT_Face_*_nose_c.0.l",
    "OPT_Face_*_nose_d.0.l",
    "OPT_Face_*_cheek_a.0.r",
    "OPT_Face_*_cheek_b.0.r",
    "OPT_Face_*_cheek_c.0.r",
    "OPT_Face_*_eye.0.r",
    "OPT_Face_*_eye_lower_a.0.r",
    "OPT_Face_*_eye_lower_b.0.r",
    "OPT_Face_*_eyebrow_a.0.r",
    "OPT_Face_*_eyebrow_b.0.r",
    "OPT_Face_*_eyebrow_c.0.r",
    "OPT_Face_*_eyelid.0.r",
    "OPT_Face_*_forehead.0.r",
    "OPT_Face_*_lip_lower.0.r",
    "OPT_Face_*_lip_outside.0.r",
    "OPT_Face_*_lip_upper.0.r",
    "OPT_Face_*_nose_a.0.r",
    "OPT_Face_*_nose_b.0.r",
    "OPT_Face_*_nose_c.0.r",
    "OPT_Face_*_nose_d.0.r",
    "OPT_Face_Root"
)

bonenames["OPT_Hand_*_Root.1.L"] = (
    "OPT_Hand_*_Index1.1.L",
    "OPT_Hand_*_Index2.1.L",
    "OPT_Hand_*_Index3.1.L",
    "OPT_Hand_*_Metacarpal04.1.L",
    "OPT_Hand_*_Middle1.1.L",
    "OPT_Hand_*_Middle2.1.L",
    "OPT_Hand_*_Middle3.1.L",
    "OPT_Hand_*_Pinky1.1.L",
    "OPT_Hand_*_Pinky2.1.L",
    "OPT_Hand_*_Pinky3.1.L",
    "OPT_Hand_*_Ring1.1.L",
    "OPT_Hand_*_Ring2.1.L",
    "OPT_Hand_*_Ring3.1.L",
    "OPT_Hand_*_Root.1.L",
    "OPT_Hand_*_Thumb1.1.L",
    "OPT_Hand_*_Thumb2.1.L",
    "OPT_Hand_*_Thumb3.1.L"
)

bonenames["OPT_Hand_*_Root.1.R"] = (
    "OPT_Hand_*_Index1.1.R",
    "OPT_Hand_*_Index2.1.R",
    "OPT_Hand_*_Index3.1.R",
    "OPT_Hand_*_Metacarpal04.1.R",
    "OPT_Hand_*_Middle1.1.R",
    "OPT_Hand_*_Middle2.1.R",
    "OPT_Hand_*_Middle3.1.R",
    "OPT_Hand_*_Pinky1.1.R",
    "OPT_Hand_*_Pinky2.1.R",
    "OPT_Hand_*_Pinky3.1.R",
    "OPT_Hand_*_Ring1.1.R",
    "OPT_Hand_*_Ring2.1.R",
    "OPT_Hand_*_Ring3.1.R",
    "OPT_Hand_*_Root.1.R",
    "OPT_Hand_*_Thumb1.1.R",
    "OPT_Hand_*_Thumb2.1.R",
    "OPT_Hand_*_Thumb3.1.R"
)

bonenames["OPT_wings_Root"] = (
    "OPT_wing_*_01.0.l",
    "OPT_wing_*_02.0.l",
    "OPT_wing_*_03.0.l",
    "OPT_wing_*_04.0.l",
    "OPT_wing_*_05.0.l",
    "OPT_wing_*_06.0.l",
    "OPT_wing_*_07.0.l",
    "OPT_wing_*_08.0.l",
    "OPT_wing_*_09.0.l",
    "OPT_wing_*_10.0.l",
    "OPT_wing_*_11.0.l",
    "OPT_wing_*_12.0.l",
    "OPT_wing_*_13.0.l",
    "OPT_wing_*_01.0.r",
    "OPT_wing_*_02.0.r",
    "OPT_wing_*_03.0.r",
    "OPT_wing_*_04.0.r",
    "OPT_wing_*_05.0.r",
    "OPT_wing_*_06.0.r",
    "OPT_wing_*_07.0.r",
    "OPT_wing_*_08.0.r",
    "OPT_wing_*_09.0.r",
    "OPT_wing_*_10.0.r",
    "OPT_wing_*_11.0.r",
    "OPT_wing_*_12.0.r",
    "OPT_wing_*_13.0.r",
    "OPT_wings_Root"
)

bonenames["OPT_uchiwa_*_Root.0.l"] = (
    "OPT_uchiwa_l",
    "OPT_uchiwa_*_Root.0.l"
)

bonenames["OPT_uchiwa_*_Root.0.r"] = (
    "OPT_uchiwa_r",
    "OPT_uchiwa_*_Root.0.r"
)

bonenames["OPT_uchiwa_bone_Root"] = (
    "OPT_uchiwa_bone_01",
    "OPT_uchiwa_bone_02",
    "OPT_uchiwa_bone_03",
    "OPT_uchiwa_bone_04",
    "OPT_uchiwa_bone_05",
    "OPT_uchiwa_bone_06",
    "OPT_uchiwa_bone_07",
    "OPT_uchiwa_bone_08",
    "OPT_uchiwa_bone_Root"
)



fglb = {'ENDIAN':"<"}#'file' = filehandle
def fread(offset = -1, fmt = 'L', extractifsingle = True):
    global fglb
    if type(offset) is str:
        if type(fmt) is bool:
            extractifsingle = fmt
        fmt = offset
    elif offset != -1:
        fglb['FILE'].seek(offset)
    result = struct.unpack(fglb['ENDIAN'] + fmt, fglb['FILE'].read(struct.calcsize("!"+fmt)))
    if extractifsingle and len(result) == 1:
        return result[0]
    return result

def freadstring(offset = -1, maxbytes = 255):
    global fglb
    if offset != -1:
        fglb['FILE'].seek(offset)
    mahbytes = b''
    count = 0
    while True:
        count += 1
        chr = fglb['FILE'].read(1)
        mahbytes += chr
        if len(chr) == 0 or count == maxbytes:
            return mahbytes[:].decode('ASCII')
        elif mahbytes[-1] == 0:
            return mahbytes[:-1].decode('ASCII')


class TmcHead():
    global fglb
    name = ""
    size = count1 = count2 = offset1 = offset2 = offset3 = base = 0
    offsets = []
    sizes = []
    def __init__(self, base):
        fglb['FILE'].seek(base)
        self.name = freadstring(base)
        self.size, self.count1, self.count2, self.count3, self.offset1, self.offset2, self.offset3 = fread(base + 0x10, '7L')
        self.base = base
        fglb['FILE'].seek(base + self.offset1)
        self.offsets = [fread('L') for i in range(self.count1)]
        if self.offset2 != 0:
            fglb['FILE'].seek(base + self.offset2)
            self.sizes = [fread('L') for i in range(self.count1)]





def set_motion_mpm(mpm_h, filename, af, obj):

    global prop

    mat_rot_z180 = mathutils.Matrix.Rotation(math.radians(180.0), 4, 'Z')
    mat_rot_z90 = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
    mat_rot_z270 = mathutils.Matrix.Rotation(math.radians(270.0), 4, 'Z')
    mat_rot_x90 = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')

    amt = obj.data

    bpy.context.view_layer.objects.active = obj

    if bpy.context.view_layer.objects.active.mode != 'EDIT': bpy.ops.object.mode_set(mode='EDIT')

    hies = {}
    bone_loc_offset = {}
    actions = []

    for i, editbone in enumerate(amt.edit_bones):
        if "MOT" not in editbone.name and "OPT_Hand_" not in editbone.name and "OPT_Face_" not in editbone.name and editbone.name not in bonenames["OPT_wings_Root"] and editbone.name not in bonenames["OPT_uchiwa_bone_Root"]:
            continue

        if editbone.parent is not None:
            if "UpLeg.1" in editbone.name:
                parent_matrix = editbone.parent.matrix @ mat_rot_z180
            elif "Shoulder.1.L" in editbone.name:
                parent_matrix = editbone.parent.matrix @ mat_rot_z270
            elif "Shoulder.1.R" in editbone.name:
                parent_matrix = editbone.parent.matrix @ mat_rot_z90
            elif "MOT_*Arm.1.L" == editbone.name and "MOT_*Shoulder.1.L" not in amt.edit_bones:
                parent_matrix = editbone.parent.matrix @ mat_rot_z270
            elif "MOT_*Arm.1.R" == editbone.name and "MOT_*Shoulder.1.R" not in amt.edit_bones:
                parent_matrix = editbone.parent.matrix @ mat_rot_z90
            elif "OPT_Face_Root" == editbone.name:
                parent_matrix = editbone.parent.matrix @ mat_rot_x90
            elif "OPT_Face_c_tongue_a" == editbone.name and "Control_tongue_loc_a" in obj.data.bones:
                parent_matrix = editbone.parent.parent.matrix
            elif "OPT_Face_c_tongue_b" == editbone.name and "Control_tongue_loc_b" in obj.data.bones:
                parent_matrix = editbone.parent.parent.matrix
            elif "OPT_wings_Root" == editbone.name:
                parent_matrix = editbone.parent.matrix @ mat_rot_z180
            elif "OPT_uchiwa_bone_01" == editbone.name:
                parent_matrix = editbone.parent.matrix @ mat_rot_z180
            else:
                parent_matrix = editbone.parent.matrix
            matrix = parent_matrix.inverted_safe() @ editbone.matrix

            if "OPT_Face_" in editbone.name:
                loc, rot, sca = (axis_conversion(to_forward='Z', to_up='-Y').to_4x4() @ matrix).decompose()
            else:
                loc, rot, sca = matrix.decompose()
            bone_loc_offset[editbone.name] = loc
        else:
            matrix = editbone.matrix

            bone_loc_offset[editbone.name] = (0,0,0)

        if "OPT_Hand_*_Thumb1.1.L" == editbone.name:
            matrix = matrix @ mat_rot_z90
        elif "OPT_Hand_*_Thumb1.1.R" == editbone.name:
            matrix = matrix @ mat_rot_z270

        if "OPT_Hand_*_Thumb1.1" in editbone.name:
            x =  matrix.to_euler()[0]
            y =  matrix.to_euler()[1]
            z = -matrix.to_euler()[2]
        elif "OPT_Hand_*_Metacarpal04.1.L" == editbone.name:
            x = -matrix.to_euler()[1]
            y = -matrix.to_euler()[0]
            z =  matrix.to_euler()[2]
        elif "OPT_Hand_*_Metacarpal04.1.R" == editbone.name:
            x =  matrix.to_euler()[1]
            y =  matrix.to_euler()[0]
            z =  matrix.to_euler()[2]
        elif "OPT_Hand_" in editbone.name and ".1.L" in editbone.name:
            x =  matrix.to_euler()[1]
            y = -matrix.to_euler()[0]
            z =  matrix.to_euler()[2]
        elif "OPT_Hand_" in editbone.name and ".1.R" in editbone.name:
            x = -matrix.to_euler()[1]
            y =  matrix.to_euler()[0]
            z =  matrix.to_euler()[2]
        elif "OPT_wing_" in editbone.name:
            x = -matrix.to_euler()[0]
            y = -matrix.to_euler()[1]
            z =  matrix.to_euler()[2]
        else:
            x = matrix.to_euler()[0]
            y = matrix.to_euler()[1]
            z = matrix.to_euler()[2]
        hies[editbone.name] = (x, y, z)

    bpy.ops.object.mode_set(mode='OBJECT')

    pose_bones = obj.pose.bones

    offset_hips = 0
    if prop["disable_rig"] and "Master" in pose_bones:
        offset_hips = pose_bones["Master"].location[1]

    for mot_idx, offset in enumerate(mpm_h.offsets):

        root_name = ""

        common_motion = False

        if offset == 0:
            continue
        mot_h = TmcHead(mpm_h.base + offset)
        uk1, acts_count, bones_count, uk2 = fread(mpm_h.base + offset + mot_h.offsets[3], '4L')
        basebone_name = freadstring()
        if basebone_name == "OPT_Hand_Left_Root":
            basebone_name = "OPT_Hand_*_Root.1.L"
        elif basebone_name == "OPT_Hand_Right_Root":
            basebone_name = "OPT_Hand_*_Root.1.R"
        #elif basebone_name == "OPT_uchiwa_l_Root":
        #    basebone_name = "OPT_uchiwa_*_Root.0.l"
        #elif basebone_name == "OPT_uchiwa_r_Root":
        #    basebone_name = "OPT_uchiwa_*_Root.0.r"
        elif basebone_name == "OPT_uchiwa_Root":
            basebone_name = "OPT_uchiwa_bone_Root"
        elif basebone_name != "MOT00_Hips" and basebone_name[:3] == "MOT":
            common_motion = True
            root_name = basebone_name
        elif basebone_name != "MOT00_Hips" and basebone_name != "OPT_Face_Root" and basebone_name != "OPT_wings_Root" and basebone_name != "OPT_uchiwa_bone_Root": #–¢‘Î‰ž‚Íœ‚­
            continue

        if basebone_name not in amt.bones:
            continue

        root_bone = pose_bones[basebone_name]

        mot4_base = mpm_h.base + offset + mot_h.offsets[4]
        mot4_offs = fread(mot4_base + fread(mot4_base + 0x20), '%dL'%fread(mot4_base + 0x14), False)
        mot4_bones_hierarchy = []
        for mot4_boneoff in mot4_offs:
            mot4_bonebase = mot4_base + mot4_boneoff
            parent_index, children_count = fread(mot4_bonebase, '2L')
            children_indices = fread(mot4_bonebase + 8, '%dL'%children_count, False)
            mot4_bones_hierarchy.append((parent_index, children_indices))

        rootidx = [p for p,c in mot4_bones_hierarchy].index(0xffffffff)

        mot0_base = mpm_h.base + offset + mot_h.offsets[0]
        af.seek(mot0_base)
        act_offsets = fread(mot0_base, '%dL'%acts_count, False)

        for act_idx, act_offset in enumerate(act_offsets):

            act_list, motion_type = parse_motion(af, bones_count, mot0_base, act_offset)

            if len(act_list) == 0:
                continue

            act_added = False

            if prop["merge_actions"] and mot_idx > 0 and basebone_name in pose_bones and len(actions) == len(act_offsets):
                act = actions[act_idx]
            else:
                act_basename = '%s-%d_%03d_%d'%(filename, mot_idx, act_idx, len(act_list[0]))
                act_name = act_basename
                count = 1
                while act_name in bpy.data.actions:
                    act_name = act_basename + "." + '{0:03d}'.format(count)
                    count += 1
                act = bpy.data.actions.new(act_name)
                act_added = True
                obj.animation_data_create()
            obj.animation_data.action = act

            if prop["merge_actions"] and mot_idx == 0:
                actions.append(act)

            if prop["use_fake_user"]:
                act.use_fake_user = True

            print('action %d/%d; frames =%d'%(act_idx + 1, acts_count, len(act_list[0])))

            bpy.ops.object.mode_set(mode='POSE')

            frm = 2

            recur_hie_bones = []

            def recur_bones_pose(bone_index, bone):
                recur_hie_bones.append((bone, bone_index))
                for i, childidx in enumerate(mot4_bones_hierarchy[bone_index][1]):
                    if basebone_name in bonenames:
                        child_bone = pose_bones[bonenames[basebone_name][childidx]]
                    else:
                        child_bone = bone.children[i]
                    recur_bones_pose(childidx, child_bone)

            recur_bones_pose(rootidx, root_bone)

            offset_face_root = None
            if motion_type != 0:
                offset_face_root = [None, None, None]

            for bone, bone_index in recur_hie_bones:

                if prop["fixed_opt_face_root"] and bone.name == "OPT_Face_Root":
                    lx,ly,lz = [act_list[bone_index * 9 + i][0][0] for i in range(3)]
                    lx,ly,lz = lx/0x004000,ly/0x004000,lz/0x004000
                    offset_face_root = [bone_loc_offset[bone.name][0] - lx, bone_loc_offset[bone.name][2] - lz, -(bone_loc_offset[bone.name][1] - ly)]
                    continue

                if prop["bones_to_visible"] and bone.bone.hide:
                    bone.bone.hide = False

                if prop["disable_rig"] and "Master" in pose_bones:
                    for constraint in bone.constraints:
                        if constraint.type == 'IK':
                            if "MOT_*ForeArm.1.L" == bone.name and "Switch_IK_Arm.L" in pose_bones:
                                pose_bones["Switch_IK_Arm.L"].location.x = 0
                            elif "MOT_*ForeArm.1.R" == bone.name and "Switch_IK_Arm.R" in pose_bones:
                                pose_bones["Switch_IK_Arm.R"].location.x = 0
                            elif "MOT_*Leg.1.L" == bone.name and "Switch_IK_Leg.L" in pose_bones:
                                pose_bones["Switch_IK_Leg.L"].location.x = 0
                            elif "MOT_*Leg.1.R" == bone.name and "Switch_IK_Leg.R" in pose_bones:
                                pose_bones["Switch_IK_Leg.R"].location.x = 0
                            constraint.influence = 0
                        elif constraint.type == 'COPY_TRANSFORMS' and ("MOT_*Hand." in bone.name or "MOT_*Foot." in bone.name):
                            if "MOT_*Hand.1.L" == bone.name and "Switch_Rot_Hand.L" in pose_bones:
                                pose_bones["Switch_Rot_Hand.L"].location.x = 0
                            elif "MOT_*Hand.1.R" == bone.name and "Switch_Rot_Hand.R" in pose_bones:
                                pose_bones["Switch_Rot_Hand.R"].location.x = 0
                            elif "MOT_*Foot.1.L" == bone.name and "Switch_Rot_Foot.L" in pose_bones:
                                pose_bones["Switch_Rot_Foot.L"].location.x = 0
                            elif "MOT_*Foot.1.R" == bone.name and "Switch_Rot_Foot.R" in pose_bones:
                                pose_bones["Switch_Rot_Foot.R"].location.x = 0
                            constraint.influence = 0

                if motion_type == 0:
                    bone.rotation_mode = 'XYZ'
                    for frm in range(len(act_list[0])):
                        skip_frame_loc = False
                        skip_frame_rot = False
                        lx,ly,lz, rx,ry,rz, sx,sy,sz = [act_list[bone_index * 9 + i][frm][0] for i in range(9)]
                        if frm > 0 and frm < len(act_list[0]) - 1:
                            plx,ply,plz, prx,pry,prz, psx,psy,psz = [act_list[bone_index * 9 + i][frm - 1][0] for i in range(9)]
                            nlx,nly,nlz, nrx,nry,nrz, nsx,nsy,nsz = [act_list[bone_index * 9 + i][frm + 1][0] for i in range(9)]

                            if lx == plx == nlx and ly == ply == nly and lz == plz == nlz:
                                skip_frame_loc = True
                            if rx == prx == nrx and ry == pry == nry and rz == prz == nrz:
                                skip_frame_rot = True
                            if (bone.name == root_name or bone.name == "MOT00_Hips" or bone.name == "OPT_uchiwa_bone_01" or "OPT_Face_" in bone.name) and skip_frame_loc and skip_frame_rot:
                                continue
                            elif bone.name != root_name and bone.name != "MOT00_Hips" and bone.name != "OPT_uchiwa_bone_01" and "OPT_Face_" not in bone.name and skip_frame_rot:
                                continue
                        lx,ly,lz = lx/0x004000,ly/0x004000,lz/0x004000
                        rx,ry,rz = rx/0x004000,ry/0x004000,rz/0x004000
                        #sx,sy,sz = sx/0x004000,sy/0x004000,sz/0x004000

                        if "OPT_Face_" in bone.name:
                            lx,ly,lz = lx - bone_loc_offset[bone.name][0], lz - bone_loc_offset[bone.name][2], -(ly - bone_loc_offset[bone.name][1])
                        elif bone.name != root_name and bone.name != "MOT00_Hips" and bone.name != "OPT_uchiwa_bone_01" and "OPT_Hand_" not in bone.name:
                            lx,ly,lz = 0,0,0
                        elif bone.name == "MOT00_Hips":
                            ly = ly - offset_hips


                        if bone.name in hies and not ("OPT_Hand_" in bone.name and "OPT_Hand_*_Root" not in bone.name):
                            rx -= hies[bone.name][0]
                            ry -= hies[bone.name][1]
                            rz -= hies[bone.name][2]

                        if bone.name != root_name and bone.name != "MOT00_Hips" and bone.name != "MOT16_Waist" and bone.name != "MOT02_Chest" and bone.name != "MOT15_Neck" and bone.name != "MOT01_Head" and "OPT_Hand_" not in bone.name:
                            if "OPT_Face_" in bone.name:
                                rx,ry,rz = rx,rz,-ry
                            elif "Shoulder.1.L" in bone.name or "Arm.1.L" in bone.name or "Hand.1.L" in bone.name:
                                rx,ry,rz = -ry,rx,rz
                            elif "Shoulder.1.R" in bone.name or "Arm.1.R" in bone.name or "Hand.1.R" in bone.name:
                                rx,ry,rz = ry,-rx,rz
                            else:
                                rx,ry,rz = -rx,-ry,rz
                        elif "OPT_Hand_*_Thumb1" in bone.name:
                            mat_loc_base = Matrix.Translation((lx,ly,lz))
                            mat_rot_base = mathutils.Matrix.Rotation(rz, 4, 'Z') * mathutils.Matrix.Rotation(ry, 4, 'Y') * mathutils.Matrix.Rotation(rx, 4, 'X')
                            mat_out = mat_loc_base * mat_rot_base
                            if ".1.L" in bone.name:
                                bone.matrix = bone.parent.matrix @ mat_rot_z90 @ mat_out @ mat_rot_z270
                            else:
                                bone.matrix = bone.parent.matrix @ mat_rot_z270 @ mat_out @ mat_rot_z90


                        mat_loc = Matrix.Translation((lx,ly,lz))

                        if bone.name == root_name or bone.name == "MOT00_Hips" or bone.name == "OPT_uchiwa_bone_01" or ("OPT_Face_" in bone.name and prop["import_face_bones_location"]):

                            if prop["fixed_opt_face_root"] and "OPT_Face_" in bone.name and bone.parent.name == "OPT_Face_Root":
                                mat_loc = Matrix.Translation((lx - offset_face_root[0],ly - offset_face_root[1],lz - offset_face_root[2]))

                            if bone.name == "OPT_Face_c_tongue_a" and "Control_tongue_loc_a" in pose_bones:
                                pose_bones["Control_tongue_loc_a"].matrix_basis =  mat_loc
                            elif bone.name == "OPT_Face_c_tongue_b" and "Control_tongue_loc_b" in pose_bones:
                                pose_bones["Control_tongue_loc_b"].matrix_basis =  mat_loc
                            else:
                                bone.matrix_basis =  mat_loc
                            if not skip_frame_loc:
                                bone.keyframe_insert(data_path='location',index=-1,frame=frm)

                        if "OPT_Face_" in bone.name:
                            bone.rotation_mode = 'ZXY'
                        elif "OPT_Hand_*_Root" in bone.name:
                            bone.rotation_mode = 'ZYX'
                        elif "Shoulder.1" in bone.name or "Arm.1" in bone.name or "Hand.1" in bone.name:
                            bone.rotation_mode = 'YXZ'

                        if "OPT_Hand_*_Thumb1" not in bone.name:
                            bone.rotation_euler = (rx, ry, rz)


                        #mat_sca = Matrix.Translation((sx,sy,sz))


                        if not skip_frame_rot:
                            bone.keyframe_insert(data_path='rotation_euler',index=-1,frame=frm)

                else:

                    if bone.name == root_name or bone.name == "MOT00_Hips" or "OPT_Face_" in bone.name:
                        fcurve_x = set_keyframe_loc(act, act_list, bone, bone_index, bone_loc_offset, 0, common_motion, offset_face_root[0])
                        fcurve_y = set_keyframe_loc(act, act_list, bone, bone_index, bone_loc_offset, 1, common_motion, offset_face_root[2])
                        fcurve_z = set_keyframe_loc(act, act_list, bone, bone_index, bone_loc_offset, 2, common_motion, offset_face_root[1])

                        if bone.name == "OPT_Face_c_tongue_a" and "Control_tongue_loc_a" in pose_bones:
                            fcurve_x.data_path = 'pose.bones["Control_tongue_loc_a"].location'
                            fcurve_y.data_path = 'pose.bones["Control_tongue_loc_a"].location'
                            fcurve_z.data_path = 'pose.bones["Control_tongue_loc_a"].location'
                        elif bone.name == "OPT_Face_c_tongue_b" and "Control_tongue_loc_b" in pose_bones:
                            fcurve_x.data_path = 'pose.bones["Control_tongue_loc_b"].location'
                            fcurve_y.data_path = 'pose.bones["Control_tongue_loc_b"].location'
                            fcurve_z.data_path = 'pose.bones["Control_tongue_loc_b"].location'

                    if "OPT_Face_" in bone.name:
                        bone.rotation_mode = 'ZXY'
                    elif "OPT_Hand_*_Root" in bone.name:
                        bone.rotation_mode = 'ZYX'
                    elif "Shoulder.1" in bone.name or "Arm.1" in bone.name or "Hand.1" in bone.name:
                        bone.rotation_mode = 'YXZ'
                    else:
                        bone.rotation_mode = 'XYZ'
                    set_keyframe_rot(act, act_list, bone, bone_index, hies, 0, common_motion, None)
                    set_keyframe_rot(act, act_list, bone, bone_index, hies, 1, common_motion, None)
                    set_keyframe_rot(act, act_list, bone, bone_index, hies, 2, common_motion, None)

            if prop["use_nla"]:
                if act_added:
                    add_nla_track(obj)
                else:
                    obj.animation_data.action = None

    if prop["disable_rig"] and "Base_Switch" in pose_bones:
        if "Switch_Eye_Track" in pose_bones:
            pose_bones["Switch_Eye_Track"].location.x = 0
        if "Switch_Around_Mouth" in pose_bones:
            pose_bones["Switch_Around_Mouth"].location.x = 0
        if "Switch_Around_Eye.l" in pose_bones:
            pose_bones["Switch_Around_Eye.l"].location.x = 0
        if "Switch_Around_Eye.r" in pose_bones:
            pose_bones["Switch_Around_Eye.r"].location.x = 0

    bpy.context.view_layer.update()


def set_keyframe_loc(act, act_list, bone, bone_index, hies, index, common_motion, offset_face_root):
    nochange_bones = ["MOT00_Hips", "MOT16_Waist", "MOT02_Chest", "MOT15_Neck", "MOT01_Head"]
    act_list_offset = index
    data_path_index = index

    if bone.name not in nochange_bones and not common_motion:
        if "OPT_Face_" in bone.name:
            if index == 0:
                data_path_index = 0
            elif index == 1:
                data_path_index = 2
            else:
                data_path_index = 1

    fcurve = act.fcurves.new(data_path='pose.bones["' + bone.name + '"].location',index=data_path_index)

    for frm, params in enumerate(act_list[bone_index * 9 + act_list_offset]):
        param = params[0]
        if param is None:
            continue
        param = param / 10000

        if bone.name in hies:
            param -= hies[bone.name][index]
        if bone.name not in nochange_bones:
            if "OPT_Face_" in bone.name:
                if data_path_index == 2:
                    param = -param
                if offset_face_root is not None and bone.parent.name == "OPT_Face_Root":
                    param = param - offset_face_root

        keyframe = fcurve.keyframe_points.insert(frame=frm, value=param, options={'FAST'})

    return fcurve


def set_keyframe_rot(act, act_list, bone, bone_index, hies, index, common_motion, offset_face_root):
    nochange_bones = ["MOT00_Hips", "MOT16_Waist", "MOT02_Chest", "MOT15_Neck", "MOT01_Head"]
    act_list_offset = index + 3
    data_path_index = index

    if bone.name not in nochange_bones and not common_motion:
        if "OPT_Face_" in bone.name:
            #rx,ry,rz = rx,rz,-ry
            if index == 0:
                data_path_index = 0
            elif index == 1:
                data_path_index = 2
            else:
                data_path_index = 1
        elif "OPT_Hand_*_Thumb1.1.L" == bone.name:
            #rx,ry,rz = rx,rz,-ry
            if index == 0:
                data_path_index = 0
            elif index == 1:
                data_path_index = 2
            else:
                data_path_index = 1
        elif "OPT_Hand_*_Thumb1.1.R" == bone.name:
            #rx,ry,rz = rz,-rx,-ry
            if index == 0:
                data_path_index = 1
            elif index == 1:
                data_path_index = 2
            else:
                data_path_index = 0
        elif "Shoulder.1.L" in bone.name or "Arm.1.L" in bone.name or ("Hand" in bone.name and ".1.L" in bone.name):
            #rx,ry,rz = -ry,rx,rz
            if index == 0:
                data_path_index = 1
            elif index == 1:
                data_path_index = 0
            else:
                data_path_index = 2
        elif "Shoulder.1.R" in bone.name or "Arm.1.R" in bone.name or ("Hand" in bone.name and ".1.R" in bone.name):
            #rx,ry,rz = ry,-rx,rz
            if index == 0:
                data_path_index = 1
            elif index == 1:
                data_path_index = 0
            else:
                data_path_index = 2

    fcurve = act.fcurves.new(data_path='pose.bones["' + bone.name + '"].rotation_euler',index=data_path_index)

    for frm, params in enumerate(act_list[bone_index * 9 + act_list_offset]):
        param = params[0]
        if param is None:
            continue
        param = param / 10000

        if bone.name in hies:
            param -= hies[bone.name][index]
        if bone.name not in nochange_bones and not common_motion:
            if "OPT_Face_" in bone.name:
                if data_path_index == 2:
                    param = -param
            elif "OPT_Hand_*_Thumb1.1.L" == bone.name:
                if data_path_index == 2:
                    param = -param
            elif "OPT_Hand_*_Thumb1.1.R" == bone.name:
                if data_path_index != 0:
                    param = -param
            elif "Shoulder.1.L" in bone.name or "Arm.1.L" in bone.name or ("Hand" in bone.name and ".1.L" in bone.name):
                if data_path_index == 0:
                    param = -param
            elif "Shoulder.1.R" in bone.name or "Arm.1.R" in bone.name or ("Hand" in bone.name and ".1.R" in bone.name):
                if data_path_index == 1:
                    param = -param
            elif data_path_index != 2:
                param = -param

        keyframe = fcurve.keyframe_points.insert(frame=frm, value=param, options={'FAST'})

    return fcurve


def parse_motion(af, bones_count, mot0_base, act_offset):
    motion_type = 0
    act_sub_offsets = fread(mot0_base + act_offset, '%dL'%(bones_count*9), False)
    act_list = []
    for act_sub_offset in act_sub_offsets:
        af.seek(mot0_base + act_sub_offset)

        val_act = []
        cc = af.read(2)
        if cc == b'\x00\x07':
            while True:
                aa = af.read(3)

                ff = aa[1] * 0x100 + aa[0]

                if   aa[2] == 0x80:     # terminator
                    bb = af.read(1)
                    val_act.append([int.from_bytes(aa[:2]+bb,'little',signed=True), None, None])
                    break

                elif aa[2] == 0x7f:     # 1 byte
                    bb = af.read(ff)
                    for i,x in enumerate(struct.unpack('<%db'%ff, bb)):
                        val_act.append([x + val_act[-1][0], None, None])

                elif aa[2] == 0x7e:     # 2 bytes
                    bb = af.read(ff*2)
                    for i,x in enumerate(struct.unpack('<%dh'%ff, bb)):
                        val_act.append([x + val_act[-1][0], None, None])

                elif aa[2] == 0x7d:     # constant
                    bb = af.read(1)
                    val_act.extend([[val_act[-1][0], None, None] for i in range(ff)])

                else:                   # 3 bytes
                    val_act.append([int.from_bytes(aa,'little',signed=True), None, None])

        else:
            motion_type = 1
            a8_frame = -1
            af.seek(mot0_base + act_sub_offset)
            while True:
                count_check_bytes = af.read(2)
                count_check = count_check_bytes[0] % 8 * 0x100 + count_check_bytes[1]
                flag_1 = count_check_bytes[0] // 8 * 8

                if flag_1 != 0 and flag_1 != 0x10 and flag_1 != 0xA8 and flag_1 != 0xF0:
                    print(hex(flag_1), "at", hex(len(act_list)), ":", hex(mot0_base + act_sub_offset), "(Unknown Flag)")

                frame_count = count_check // 4
                flag_2 = count_check % 4

                if flag_1 == 0xA8 and flag_2 != 3:
                    print(flag_2, "at", hex(mot0_base + act_sub_offset), "(Unknown Flag 0xA8)")

                if flag_1 == 0xA8 or flag_1 == 0x98 or flag_1 == 0x48:
                    if flag_1 == 0xA8:
                        val_bytes = af.read(10)
                    elif flag_1 == 0x98:
                        val_bytes = af.read(8)
                    elif flag_1 == 0x48:
                        val_bytes = af.read(4)

                    val_act.append([int.from_bytes(val_bytes[:4],'big',signed=True), None, None])
                    a8_frame = len(val_act)
                    for i in range(frame_count - 1):
                        val_act.append([None, None, None])

                elif flag_2 == 0 or flag_2 == 1 or flag_2 == 3:
                    if flag_2 == 3:
                        val_bytes = af.read(6)
                    else:
                        val_bytes = af.read(2)

                    if flag_1 > 0x7F:
                        val = int.from_bytes((flag_1 // 0x10 + 0xF0).to_bytes(1, 'big') + val_bytes[:2],'big',signed=True)
                    else:
                        val = int.from_bytes((flag_1 // 0x10).to_bytes(1, 'big') + val_bytes[:2],'big',signed=False)

                    val_act.append([val, None, None])
                    if a8_frame != -1:
                        val_act[a8_frame][0] = val
                        a8_frame = -1

                    if flag_2 == 0:
                        break
                    else:
                        for i in range(frame_count - 1):
                            val_act.append([None, None, None])

        act_list.append(val_act)

    return act_list, motion_type



def set_motion_cam(cam_base, filename):

    global prop

    info_offsets_offset = fread(cam_base + 4)
    info_offsets = []
    count = 0
    while True:
        info_offset = fread(cam_base + info_offsets_offset + (4 * count), 'L')
        if info_offset == 0:
            break
        info_offsets.append(info_offset)
        count += 1

    if bpy.context.active_object is not None and not bpy.context.active_object.hide_viewport:
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.add(type='EMPTY')
    parent = bpy.context.active_object
    parent.name = "Camera_%s_Parent" % (filename)
    parent.empty_display_size = prop["parent_scale"]
    parent.lock_rotation = (True, True, True)

    bpy.ops.object.add(type='EMPTY')
    por = bpy.context.active_object
    por.name = "Camera_%s_POR" % (filename)
    por.empty_display_size = prop["por_scale"]
    por.lock_rotation = (True, True, True)

    if prop["target_camera"] == None:
        bpy.ops.object.add(type='CAMERA')
        cam = bpy.context.active_object
        cam.name = "Camera_%s"%(filename)
        cam.data.name = "Camera_%s_Data"%(filename)
    else:
        cam = prop["target_camera"]
        cam.constraints.clear()
        cam.rotation_mode = 'XYZ'
        cam.rotation_euler = (0, 0, 0)
        cam.location = (0, 0, 0)

    cam.parent = parent
    cam.data.display_size = 0.25
    cam.lock_location = (True, True, True)
    cam.lock_rotation = (True, True, False)

    parent.constraints.new('TRACK_TO')
    parent.constraints.active.target = por
    parent.constraints.active.track_axis = 'TRACK_NEGATIVE_Z'
    parent.constraints.active.up_axis = 'UP_Y'


    for mot_idx, offset in enumerate(info_offsets):
        frame_count, unknown, por_offset, cam_offset, tilt_offset, angle_offset = fread(cam_base + offset, '6L')
        if frame_count == 0:
            continue

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = por
        por.select_set(True)

        act_basename = 'Camera_%s-%d_%d_POR'%(filename, mot_idx, frame_count)
        act_name = act_basename
        count = 1
        while act_name in bpy.data.actions:
            act_name = act_basename + "." + '{0:03d}'.format(count)
            count += 1
        bpy.data.actions.new(act_name)
        if prop["use_fake_user"]:
            bpy.data.actions[act_name].use_fake_user = True
        por.animation_data_create()
        por.animation_data.action = bpy.data.actions[act_name]

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = parent
        parent.select_set(True)

        act_basename = 'Camera_%s-%d_%d_Parent'%(filename, mot_idx, frame_count)
        act_name = act_basename
        count = 1
        while act_name in bpy.data.actions:
            act_name = act_basename + "." + '{0:03d}'.format(count)
            count += 1
        bpy.data.actions.new(act_name)
        if prop["use_fake_user"]:
            bpy.data.actions[act_name].use_fake_user = True
        parent.animation_data_create()
        parent.animation_data.action = bpy.data.actions[act_name]

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = cam
        cam.select_set(True)

        act_basename = 'Camera_%s-%d_%d'%(filename, mot_idx, frame_count)
        act_name = act_basename
        count = 1
        while act_name in bpy.data.actions:
            act_name = act_basename + "." + '{0:03d}'.format(count)
            count += 1
        bpy.data.actions.new(act_name)
        if prop["use_fake_user"]:
            bpy.data.actions[act_name].use_fake_user = True
        cam.animation_data_create()
        cam.animation_data.action = bpy.data.actions[act_name]

        act_basename = 'Camera_%s-%d_%d_Data'%(filename, mot_idx, frame_count)
        act_name = act_basename
        count = 1
        while act_name in bpy.data.actions:
            act_name = act_basename + "." + '{0:03d}'.format(count)
            count += 1
        bpy.data.actions.new(act_name)
        if prop["use_fake_user"]:
            bpy.data.actions[act_name].use_fake_user = True
        cam.data.animation_data_create()
        cam.data.animation_data.action = bpy.data.actions[act_name]


        for frm in range(frame_count):

            keyframe_loc = True
            keyframe_por = True
            keyframe_tilt = True
            keyframe_angle = True

            cam_x, cam_y, cam_z = fread(cam_base + cam_offset + (12 * frm), '3f')
            por_x, por_y, por_z = fread(cam_base + por_offset + (12 * frm), '3f')
            tilt = fread(cam_base + tilt_offset + (4 * frm), 'f')
            angle = fread(cam_base + angle_offset + (4 * frm), 'f')

            if frm != 0 and frm != frame_count - 1:
                p_cam_x, p_cam_y, p_cam_z = fread(cam_base + cam_offset + (12 * (frm - 1)), '3f')
                n_cam_x, n_cam_y, n_cam_z = fread(cam_base + cam_offset + (12 * (frm + 1)), '3f')
                if cam_x == p_cam_x == n_cam_x and cam_y == p_cam_y == n_cam_y and cam_z == p_cam_z == n_cam_z:
                    keyframe_loc = False
                p_por_x, p_por_y, p_por_z = fread(cam_base + por_offset + (12 * (frm - 1)), '3f')
                n_por_x, n_por_y, n_por_z = fread(cam_base + por_offset + (12 * (frm + 1)), '3f')
                if por_x == p_por_x == n_por_x and por_y == p_por_y == n_por_y and por_z == p_por_z == n_por_z:
                    keyframe_por = False
                p_tilt = fread(cam_base + tilt_offset + (4 * (frm - 1)), 'f')
                n_tilt = fread(cam_base + tilt_offset + (4 * (frm + 1)), 'f')
                if tilt == p_tilt == n_tilt:
                    keyframe_tilt = False
                p_angle = fread(cam_base + angle_offset + (4 * (frm - 1)), 'f')
                n_angle = fread(cam_base + angle_offset + (4 * (frm + 1)), 'f')
                if angle == p_angle == n_angle:
                    keyframe_angle = False

            if keyframe_angle:
                cam.data.angle_y = math.radians(angle)
                cam.data.keyframe_insert(data_path='lens',index=-1,frame=frm)

            if keyframe_loc:
                parent.location = (cam_x, -cam_z, cam_y)
                parent.keyframe_insert(data_path='location',index=-1,frame=frm)

            if keyframe_tilt:
                cam.rotation_euler = (0, 0, math.radians(-tilt))
                cam.keyframe_insert(data_path='rotation_euler', index=2, frame=frm)

            if keyframe_por:
                por.location = (por_x, -por_z, por_y)
                por.keyframe_insert(data_path='location',index=-1,frame=frm)

        if prop["use_nla"]:
            add_nla_track(por)
            add_nla_track(parent)
            add_nla_track(cam)
            add_nla_track(cam.data)

    bpy.context.view_layer.objects.active = cam
    area = None
    for ar in bpy.context.screen.areas:
        if ar.type == 'VIEW_3D':
            area = ar
            break
    new_ctx = bpy.context.copy()
    new_ctx["area"] = area
    bpy.ops.view3d.object_as_camera(new_ctx)

    if prop["set_resolution"]:
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080


def add_nla_track(obj):
    new_track = obj.animation_data.nla_tracks.new()
    new_track.name = "Track" + str(len(obj.animation_data.nla_tracks) - 1)
    new_track.strips.new("", 0, obj.animation_data.action)
    if obj.animation_data.action.name[:7] == "Camera_" and len(obj.animation_data.nla_tracks) > 1:
        new_track.mute = True
    obj.animation_data.action = None


def set_motion(filepath):

    global prop

    with open(filepath, 'rb') as af:
        mpmdata = af.read()
    with io.BytesIO(mpmdata) as af:
        fglb['FILE'] = af

        basename = os.path.basename(filepath)

        if basename[-7:].lower() == ".tdpack":
            filename = basename[:-7]
        elif basename[-4:].upper() == ".MPM":
            filename = basename[:-4]
        elif basename[-4:].upper() == ".CAM":
            filename = basename[:-4]
        else:
            filename = basename

        mpm_h = None
        cam_base = -1

        if filepath[-4:].upper() == ".CAM":
            cam_base = 0
        else:
            header_name = freadstring(0, 8)
            if header_name == "tdpack":
                tdp_h = TmcHead(0)
                if tdp_h.offsets[1] != 0:
                    cam_base = tdp_h.offsets[1]
                if tdp_h.offsets[2] != 0:
                    mpm_h = TmcHead(tdp_h.offsets[2])
            elif header_name == "char_dat":
                mpm_h = TmcHead(0)
            else:
                return

        if prop["bone_motion"] and mpm_h is not None:
            for ob in prop["target_armatures"]:
                set_motion_mpm(mpm_h, filename, af, ob)

        if prop["camera_motion"] and cam_base != -1:
            set_motion_cam(cam_base, filename)


def collect_objects():
    global armatures
    global subarmatures
    global cameras

    armatures = []
    subarmatures = []
    cameras = []

    for obj in bpy.context.selectable_objects:
        if obj.type == 'ARMATURE':
            armatures.append(obj)
            subarmatures.append(obj)
        elif obj.type == 'CAMERA':
            cameras.append(obj)


def get_armature_object_callback(self, context):
    global armatures
    items = []
    for i, armature in enumerate(armatures):
        item = (str(i), armature.name, "")
        items.append(item)
    return items


def get_subarmature_object_callback(self, context):
    global subarmatures
    items = []
    item = ("None", "None", "")
    items.append(item)
    for i, armature in enumerate(subarmatures):
        item = (str(i), armature.name, "")
        items.append(item)
    return items


def get_camera_object_callback(self, context):
    global cameras
    items = []
    item = (str(0), "New", "")
    items.append(item)
    for i, camera in enumerate(cameras):
        item = (str(i + 1), camera.name, "")
        items.append(item)
    return items


class Import_doa5pc_motion(Operator, ImportHelper):
    """Import doa5pc motion"""
    bl_idname = "import.doa5pc_motion"
    bl_label = "Import DOA5PC Motion"
    bl_options = {'UNDO'}
    #filename_ext = ".MPM"

    filter_glob: StringProperty(
            default="*.MPM;*.CAM;*.tdpack",
            options={'HIDDEN'}
            )

    bone_motion: BoolProperty(
            name="Import Bone Motion",
            description="Import Bone Motion if Data in File",
            default=True,
            )

    target_armature: EnumProperty(
            name="",
            items=get_armature_object_callback,
            description="1st Target Armature Object",
            )

    subtarget_armature: EnumProperty(
            name="",
            items=get_subarmature_object_callback,
            description="2nd Target Armature Object",
            )

    import_face_bones_location: BoolProperty(
            name="Import Face Bones Location",
            description="Import Face Bones Location",
            default=True,
            )

    fixed_opt_face_root: BoolProperty(
            name="Fixed \"OPT_Face_Root\"",
            description="Fixed \"OPT_Face_Root\"",
            default=False,
            )

    bones_to_visible: BoolProperty(
            name="Motion Bones to Visible",
            description="Switch Motion Bones to Visible if Hidden",
            default=True,
            )

    merge_actions: BoolProperty(
            name="Merge Actions",
            description="Merge Actions",
            default=True,
            )

    disable_rig: BoolProperty(
            name="Disable Rig",
            description="Disable Rig",
            default=True,
            )

    camera_motion: BoolProperty(
            name="Import Camera Motion",
            description="Import Camera Motion if Data in File",
            default=True,
            )

    target_camera: EnumProperty(
            name="Camera",
            items=get_camera_object_callback,
            description="Target Camera Object",
            )

    parent_scale: FloatProperty(
            name="Scale of Parent of Camera",
            description="Scale of Parent Object of Camera Object",
            default=0.5,
            )

    por_scale: FloatProperty(
            name="Scale of POR",
            description="Scale of POR Object",
            default=0.25,
            )

    set_resolution: BoolProperty(
            name="Set Resolution",
            description="Set Resolution to 1080P",
            default=True,
            )

    use_nla: BoolProperty(
            name="Use NLA",
            description="Use NLA",
            default=True,
            )

    use_fake_user: BoolProperty(
            name="Use Fake User",
            description="Use Fake User",
            default=True,
            )

    set_frame_start_to_0: BoolProperty(
            name="Set Start Frame to 0",
            description="Set Start Frame to 0",
            default=True,
            )

    set_frame_preview_start_to_0: BoolProperty(
            name="Set Preview Start Frame to 0",
            description="Set Preview Start Frame to 0",
            default=True,
            )

    set_frame_end_to_max: BoolProperty(
            name="Set End Frame to Max",
            description="Set End Frame to Max",
            default=True,
            )

    set_frame_preview_end_to_max: BoolProperty(
            name="Set Preview End Frame to Max",
            description="Set Preview End Frame to Max",
            default=True,
            )

    set_current_frame_to_0: BoolProperty(
            name="Set Current Frame to 0",
            description="Set Current Frame to 0",
            default=True,
            )

    def draw(self, context):
        global armatures

        layout = self.layout
        col_bone = layout.column()
        col_bone.prop(self, "bone_motion")
        col_bone_option = col_bone.column()

        col_bone_option.prop(self, "target_armature")
        col_bone_option.prop(self, "subtarget_armature")

        col_bone_option.prop(self, "import_face_bones_location")
        col_face_bone_option = col_bone_option.column()
        col_face_bone_option.prop(self, "fixed_opt_face_root")

        col_face_bone_option.enabled = self.import_face_bones_location

        col_bone_option.prop(self, "bones_to_visible")
        col_bone_option.prop(self, "merge_actions")

        if len(armatures) == 0:
            col_bone.enabled = False
            self.bone_motion = False
            col_bone_option.enabled = False
        elif not self.bone_motion:
            col_bone_option.enabled = False

        col_disable_rig = layout.column()
        col_disable_rig.prop(self, "disable_rig")
        if not col_bone_option.enabled or ("Master" not in armatures[int(self.target_armature)].data.bones and "Base_Switch" not in armatures[int(self.target_armature)].data.bones and (self.subtarget_armature == "None" or ("Master" not in subarmatures[int(self.subtarget_armature)].data.bones and "Base_Switch" not in subarmatures[int(self.subtarget_armature)].data.bones))):
            col_disable_rig.enabled = False

        layout.separator()

        col_camera = layout.column()
        col_camera.prop(self, "camera_motion")
        col_camera_option = col_camera.column()
        col_camera_option.prop(self, "target_camera")

        col_camera_option.prop(self, "parent_scale")
        col_camera_option.prop(self, "por_scale")
        col_camera_option.prop(self, "set_resolution")

        if not self.camera_motion:
            col_camera_option.enabled = False

        layout.separator()

        layout.prop(self, "use_nla")
        col_use_fake_user = layout.column()
        col_use_fake_user.prop(self, "use_fake_user")
        if not self.use_nla:
            col_use_fake_user.enabled = False
            self.use_fake_user = True

        layout.separator()

        layout.prop(self, "set_frame_start_to_0")
        layout.prop(self, "set_frame_preview_start_to_0")
        layout.prop(self, "set_frame_end_to_max")
        layout.prop(self, "set_frame_preview_end_to_max")
        layout.prop(self, "set_current_frame_to_0")

    def check(self, context):
        global set_default_target
        global armatures
        global subarmatures
        global cameras

        if set_default_target:
            collect_objects()
            set_default_target = False
            setted = False
            for i, armature in enumerate(armatures):
                if armature.select_get():
                    if setted:
                        self.subtarget_armature = str(i)
                    else:
                        self.target_armature = str(i)
                        setted = True
            for i, camera in enumerate(cameras):
                if camera.select_get():
                    self.target_camera = str(i + 1)
        return True

    def execute(self, context):
        global prop

        if self.filepath[-6:].lower() == ".blend":
            return {"CANCELLED"}

        prop = {}

        prop["bone_motion"] = self.bone_motion
        prop["import_face_bones_location"] = self.import_face_bones_location
        prop["fixed_opt_face_root"] = self.fixed_opt_face_root
        prop["bones_to_visible"] = self.bones_to_visible
        prop["merge_actions"] = self.merge_actions
        prop["disable_rig"] = self.disable_rig

        prop["camera_motion"] = self.camera_motion
        prop["parent_scale"] = float(self.parent_scale)
        prop["por_scale"] = float(self.por_scale)
        prop["set_resolution"] = self.set_resolution

        prop["use_nla"] = self.use_nla
        prop["use_fake_user"] = self.use_fake_user

        prop["set_frame_start_to_0"] = self.set_frame_start_to_0
        prop["set_frame_preview_start_to_0"] = self.set_frame_preview_start_to_0
        prop["set_frame_end_to_max"] = self.set_frame_end_to_max
        prop["set_frame_preview_end_to_max"] = self.set_frame_preview_end_to_max
        prop["set_current_frame_to_0"] = self.set_current_frame_to_0

        if self.bone_motion:
            prop["target_armatures"] = []
            prop["target_armatures"].append(armatures[int(self.target_armature)])
            if self.subtarget_armature != "None" and armatures[int(self.target_armature)] != subarmatures[int(self.subtarget_armature)]:
                prop["target_armatures"].append(subarmatures[int(self.subtarget_armature)])
        if self.camera_motion:
            if int(self.target_camera) == 0:
                prop["target_camera"] = None
            else:
                prop["target_camera"] = cameras[int(self.target_camera) - 1]

        if prop["set_frame_start_to_0"]:
            bpy.context.scene.frame_start = 0
        if prop["set_frame_preview_start_to_0"]:
            bpy.context.scene.frame_preview_start = 0

        cur_action_len = len(bpy.context.blend_data.actions)

        set_motion(self.filepath)

        if len(bpy.context.blend_data.actions) > cur_action_len and (prop["set_frame_end_to_max"] or prop["set_frame_preview_end_to_max"]):
            end_frame = 1
            actions = bpy.context.blend_data.actions
            for i in range(cur_action_len, len(actions)):
                if end_frame < actions[i].frame_range[1]:
                    end_frame = actions[i].frame_range[1]
            if prop["set_frame_end_to_max"]:
                bpy.context.scene.frame_end = end_frame
            if prop["set_frame_preview_end_to_max"]:
                bpy.context.scene.frame_preview_end = end_frame

        if prop["set_current_frame_to_0"]:
            bpy.context.scene.frame_set(0)

        return {"FINISHED"}



classes = (
    Import_doa5pc_motion,
)

def menu_func(self, context):
    global prop
    global set_default_target
    global armatures
    global cameras

    set_default_target = True

    self.layout.operator(Import_doa5pc_motion.bl_idname, text="DOA5PC Motion", icon='PLUGIN')

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()
