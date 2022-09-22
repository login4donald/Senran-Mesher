bl_info = {
    "name": "Senran Kagura Blender Mesher (Experimental) r. 0050",
    "author": "bluesnowball18 + loggey",
    "version": (0, 6),
    "blender": (3, 2, 1),
    "description": "Senran Kagura: Estival and BURST model editor in Development."
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

import struct
import math
import sys

def import_cat_file(filepath):

    file = open(filepath, "rb")

    file.seek(0x400)
    names = file.read(256).decode("ascii").split(",\r\n")
    del names[-1:]

    names_index = 1
    file_seek = 0x500
    file_end = 0x00
    hasEffectJoint = False
    isCharacterModel = False


    for name in names:
        magic, = struct.unpack("I", file.read(4))

        # Identifiers

        file.seek(2, 1)
        verts_format, verts_format_2 = struct.unpack("BB", file.read(2))

        ## ================= START DEBUG BLOCK =================

        # Bounding Box Start?
        file.seek(32, 1)
        unknown1, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 1:", hex(unknown1))

        # BVH Data Start?
        file.seek(20, 1)
        unknown2, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 2:", hex(unknown2))

        # there are two more addresses.

        # BVH Data Start?
        file.seek(20, 1)
        unknown3, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 3:", hex(unknown3))

        # Loading Start?
        file.seek(4, 1)
        unknown4, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 4:", hex(unknown4))

        # Unknown Start?
        file.seek(4, 1)
        unknown5, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 5:", hex(unknown5))

        # Rigging-Data Start?
        file.seek(4, 1)
        faces_start, = struct.unpack("I", file.read(4))

        # Unknown Start?
        file.seek(4, 1)
        unknown6, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 6:", hex(unknown6))
        #print(" -", unknown6)

        # PolyGroup Start?
        file.seek(12, 1)
        unknown7, = struct.unpack("I", file.read(4))
        #print("Unknown Start Value 7:", hex(unknown7))
        #print(" -", unknown7)

        file.seek(4, 1)

        ## ================= END DEBUG BLOCK =================

        ##file.seek(28, 1)
        verts_start, = struct.unpack("I", file.read(4))

        file.seek(56, 1)
        faces_count, = struct.unpack("I", file.read(4))

        file.seek(12, 1)
        verts_count, = struct.unpack("I", file.read(4))

        verts = []
        faces = []
        uvs = []
        uvmap = []

        # Padding Set

        if verts_format == 0x9F and verts_format_2 == 0x74:
            # Player/Hair
            verts_padding = 28

        elif verts_format == 0x97 and verts_format_2 == 0x74:
            # Weapon(s)
            verts_padding = 20
            hasEffectJoint = True
            # en17_*, Costume (except Bura)

        elif verts_format == 0xBF and verts_format_2 == 0x74:
            # Costume(s)
            verts_padding = 32
            isCharacterModel = True

        elif verts_format == 0x9F and verts_format_2 == 0x50:
            # Accessory/ies
            verts_padding = 20

        elif verts_format == 0xB7 and verts_format_2 == 0x50:
            # Objects
            verts_padding = 16

        elif verts_format == 0xB7 and verts_format_2 == 0x58:
            # Background/Scenes
            verts_padding = 16

        else:
            return

        # Vertex & UV data -- Known Working

        file.seek(file_seek + verts_start)
        i = 0

        while i < verts_count:
            x, z, y = struct.unpack("fff", file.read(12))
            verts.append((x, -y, z))

            file.seek(verts_padding-4, 1)
            u, v = struct.unpack("HH", file.read(4))
            uvs.append(((u)/1024, float((-v)/1024)+1))

            i += 1
            if i == verts_count:
                file_end = int(file.tell())

        # Face/Triangle data -- Known Working

        file.seek(file_seek + faces_start)
        i = 0

        if verts_format_2 != 0x58:
            while i < faces_count:
                newFace = struct.unpack("HHH", file.read(6))
                faces.append(newFace)

                # Organize the UV corrdinates proper in the uvmap
                uvmap.append(uvs[newFace[0]])
                uvmap.append(uvs[newFace[1]])
                uvmap.append(uvs[newFace[2]])

                i += 1
        else:
            while i < faces_count:
                newFace = struct.unpack("III", file.read(12))
                faces.append(newFace)

                i += 1
            if i == faces_count:
                print(file.tell())

        # Prep for other mesh

        file.seek(file_end)

        if len(names) > 1:
            file_seek = file.tell() + 256 - 1 - (file.tell() + 256 - 1) % 256

        file.seek(file_seek)

        ## Create seperate mesh

        mesh = bpy.data.meshes.new(names[names_index-1])
        mesh.from_pydata(verts, [], faces)

        object = bpy.data.objects.new(names[names_index-1], mesh)
        bpy.context.collection.objects.link(object)

        ## Simple Smooth Mesh

        mesh = object.data
        mesh.auto_smooth_angle = math.radians(90)

        for f in mesh.polygons:
            f.use_smooth = True

        ## Apply materials

        mat = bpy.data.materials.new(name=names[names_index-1])

        if object.data.materials:
            object.data.materials[0] = mat
        else:
            object.data.materials.append(mat)

        #print()
        #print("Statistics_____")
        #print(" Vert count*:", verts_count)
        #print(" Edges count:", len(mesh.edges))
        #print(" Face count*:", faces_count)
        ##print(" UVs len:", len(uvs)) #Same as Vert count
        #print(" Mesh loops:", len(mesh.loops))
        ##print(" Mesh polys:", len(mesh.polygons)) #Same as Face count
        #print(" _____Finished mesh", names_index, "of", len(names))

        # Pass on the uvmap to the mesh

        newUV = mesh.uv_layers.new(name=names[names_index-1])

        w = 0
        while w < len(uvmap):
            newUV.data[w].uv = uvmap[w]
            w += 1

        print()

        ## Iterate to the next data stream

        names_index += 1

    file.close()
    print("Complete.")




# START debug_export -- METHOD HERE --↓

def export_cat_file(filepath):
    file = open(filepath, "wb")

    # Write File header

    file.write(b'\x01\x00\x00\x00')
    file.write(b'\x01\x00\x00\x00')
    file.write(b'\x00\x00\x00\x00')
    file.write(b'\x01\x00\x00\x00')

    file.write(b'\x00\x00\x00\x00')
    file.write(b'\x00\x00\x00\x00')
    file.write(b'\x03\x00\x00\x00')
    file.write(b'\x00\x00\x00\x00')

    # Move to default starting location

    file.seek(0x400)

    names = []
    mc = 0
    i = 0

    # Get all mesh in scene

    objects = bpy.context.scene.objects
    tmd_viable_mesh = []

    for obj in objects:
        if obj.type == 'MESH':
            tmd_viable_mesh.append(obj)

    # Return mesh count

    print("Mesh Count:", len(tmd_viable_mesh))

    # Write the Object names

    while mc < len(tmd_viable_mesh):
        file.write(tmd_viable_mesh[mc].name.encode('ascii'))
        i += len(tmd_viable_mesh[mc].name)
        file.write(b'\x2C\x0D\x0A')
        i += len(b'\x2C\x0D\x0A')
        mc += 1

    # Fill empty place until next *00 offset

    fill = 256-(i)
    file.seek(fill, 1)

    # Write basic mesh data sequentially

    mc = 0
    file_seek = 0x500
    verts_padding = 0

    while mc < len(tmd_viable_mesh):

        mesh = tmd_viable_mesh[mc].data

        verts = mesh.vertices
        faces = mesh.polygons
        uvmap = mesh.uv_layers.active.data
        uvs = []

        #magic,
        file.write(b"tmd0")

        #vert formats,
        file.seek(2, 1)
        file.write(struct.pack("BB", int("0x9F", 16), int("0x74", 16)))

        #header filler
        file.seek (2, 1)
        file.write(struct.pack("BB", int("0x01", 16), int("0x02", 16)))
        file.write(struct.pack("HH", int(40), int(65535)))

        verts_padding = 20

        ## Set simple & known identifiers

        file.seek(100, 1)   # default: 104
        face_seek_loc = file.tell()
        print("Face Start Loc:", hex(face_seek_loc))
        # temp

        file.seek(28, 1)
        vert_seek_loc = file.tell()
        print("Vert Start Loc:", hex(vert_seek_loc))
        # temp

        file.seek(56, 1)
        face_count = int(len(faces))
        file.write(struct.pack("I", face_count))

        file.seek(16, 1)    # default: 12
        vert_count = int(len(verts))
        file.write(struct.pack("I", vert_count))
        print(len(verts))

        # Write vertexes

        file.seek(file_seek + tmp1)
        i = 0

        while i < face_count:
            v3 = struct.pack("HHH", int(faces[i].vertices[0]), int(faces[i].vertices[1]), (int(faces[i].vertices[2])))
            i += 1

        i = 0
        while i < vert_count:
            v3 = struct.pack("fff", float(verts[i].co.x), float(verts[i].co.z), (float(verts[i].co.y)))

            file.write(v3)
            #print(v3)

            file.seek(verts_padding, 1)
            #print(uvmap[i].uv)

            u = uvmap[i].uv.x * 1024
            v = ((uvmap[i].uv.y * 1024))+1

            v2 = struct.pack("HH", int(u), int(v))
            file.write(v2)

            print("Writing", v2, "UV Coord", i,"at", hex(file.tell()))

            i += 1

        print("Finished vertices.")

        new_face_seek_loc = file.tell()
        file.seek(face_seek_loc)
        file.write(struct.pack("I", int(new_face_seek_loc)))
        file.seek(new_face_seek_loc)


        #file.seek()
        # Prepare for the next avaliable \x00 offset

        new_seek = file.tell() + 256 - 1 - (file.tell() + 256 - 1) % 256
        file.seek(new_seek)

        mc += 1

    ## Write \x00 to the end
    new_seek = file.tell() + 256 - 1 - (file.tell() + 256 - 1) % 256
    file.write(struct.pack("B", 00))

    file.close()

    print("Export Debug Complete")

# END debug_export -- METHOD HERE --↑

class ESM_MT_import_cat(Operator, ImportHelper):
    bl_idname = "import.cat"
    bl_label = "Import CAT"

    filename_ext = ".cat"

    def execute(self, operator):
        import_cat_file(self.properties.filepath)
        return { "FINISHED" }

# START debug_export -- development

class ESM_MT_export_cat(Operator, ExportHelper):
    bl_idname = "export.cat"
    bl_label = "Export CAT"

    filename_ext = ".cat"

    type: EnumProperty(
        name="Model Type",
        description="The type of game model you are exporting.",
        items=(
            ('PL', "Player/Hair", "Models for the face or hair"),
            ('WP', "Weapon", "Models for the weapon(s)"),
            ('CO', "Costume", "Models for the costume"),
            ('AC', "Accessory", "Model for the sccessory"),
            ('OB', "Object", "Model for the objects"),
            ('BG', "Field", "Model for the field or stage")
        ),
        default='PL',
    )

    def execute(self, operator):
        export_cat_file(self.properties.filepath)
        return { "FINISHED" }

# FINISH debug_export -- development

def menu_func(self, context):
    self.layout.operator(ESM_MT_import_cat.bl_idname, text = "Senran Kagura EV/BRN/PBS CAT (.cat)")

# debug_export
def menu_ex_func(self, context):
    self.layout.operator(ESM_MT_export_cat.bl_idname, text = "Senran Kagura EV/BRN/PBS CAT (.cat) (non-functional)")

def register():
    bpy.utils.register_class(ESM_MT_import_cat)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)
    # debug_export
    bpy.utils.register_class(ESM_MT_export_cat)
    bpy.types.TOPBAR_MT_file_export.append(menu_ex_func)

def unregister():
    bpy.utils.unregister_class(ESM_MT_import_cat)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    # debug_export
    bpy.utils.unregister_class(ESM_MT_export_cat)
    bpy.types.TOPBAR_MT_file_export.remove(menu_ex_func)

if __name__ == "__main__":
    register()
