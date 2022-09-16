bl_info = {
        "name": "BURST Renewal Model Tool v0.3-alpha",
        "author": "bluesnowball18 + loggey",
        "version": (0, 3),
        "blender": (3, 2, 1),
        "description": "Senran Kagura: BURST Renewal file editor"
}

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

import struct

def import_cat_file(filepath):
        file = open(filepath, "rb")

        file.seek(0x400)
        names = file.read(256).decode("ascii").split(",\r\n")

        del names[-1:]

        # go to number section of tmd0 header
        # file.seek(0x528)

        magic, = struct.unpack("I", file.read(4))

        file.seek(2, 1)
        verts_format, verts_format_2 = struct.unpack("BB", file.read(2))



        file.seek(104, 1)
        faces_start, = struct.unpack("I", file.read(4))

        #file.seek(4, 1)
        #uvs_start, = struct.unpack("I", file.read(4))

        file.seek(28, 1)
        verts_start, = struct.unpack("I", file.read(4))

        #file.seek(28, 1)
        #verts_start, = struct.unpack("I", file.read(4))




        file.seek(56, 1)
        faces_count, = struct.unpack("I", file.read(4))

        #file.seek(12, 1)
        #uvs_count, = struct.unpack("I", file.read(4))

        file.seek(12, 1)
        verts_count, = struct.unpack("I", file.read(4))

        #file.seek(12, 1)
        #verts_count, = struct.unpack("I", file.read(4))



        verts = []
        faces = []
        # !
        uvs = []

        print()
        print("File Name:", names[0])
        print()
        print("vertexs:", verts_count)
        print("faces:", faces_count)
        #print("uv coords:", uvs_count)
        print()
        # pl*, hr*, en* (except en17_*)
        if verts_format == 0x9F and verts_format_2 == 0x74:
                print("-- Player/Hair Detected.")
                verts_padding = 28
        # TODO: add support for wpn*
        # elif verts_format == 0x97 and verts_format_2 == 0x74:
        #        verts_padding = 20
        # en17_*, Costume (except Bura)
        elif verts_format == 0xBF and verts_format_2 == 0x74:
                print("-- Costume Detected.")
                verts_padding = 32
        # acce_*
        elif verts_format == 0x9F and verts_format_2 == 0x50:
                print("-- Accessory Detected.")
                verts_padding = 20
        # obj*
        elif verts_format == 0xB7 and verts_format_2 == 0x50:
                print("-- Object Detected.")
                verts_padding = 16
        # bg*
        elif verts_format == 0xB7 and verts_format_2 == 0x58:
                print("-- Background Detected.")
                verts_padding = 16
        else:
                return

        file.seek(0x500 + verts_start)
        print("Vertex Start Position:", hex(file.tell()))

        i = 0

        while i < verts_count:
                x, z, y = struct.unpack("fff", file.read(12))

                # verts.append(struct.unpack("fff", file.read(12)))
                verts.append((x, -y, z))

                i += 1
                file.seek(verts_padding, 1)
                if i == verts_count:
                    print("Vertex Final Position:", hex(file.tell()))


        print("-- Vertices Completed.")
        print()

        file.seek(0x500 + faces_start)
        print("Face Start Position:", hex(file.tell()))

        i = 0

        if verts_format_2 != 0x58:
                while i < faces_count:
                        faces.append(struct.unpack("HHH", file.read(6)))
                        i += 1
                        if i == faces_count:
                                # print("Vertex Format: 0x58")
                                print("Face Final Position:", hex(file.tell()))
        else:
                while i < faces_count:
                        faces.append(struct.unpack("III", file.read(12)))
                        i += 1
                        if i == faces_count:
                                # print("Vertex Format: NOT 0x58")
                                print("Face Final Position:", hex(file.tell()))

        print("-- Faces Completed.")
        print()

        ## adding mapping support?
        #file.seek(0x500 + uvs_start)
        #i = 0

        #while i < uvs_count:
            #x, z, y = struct.unpack("fff", file.read(12))
            #print ("vert ", i, " : ", (x, -y, z))
            #uvs.append((x, -y, z))
            #i += 1

        ##

        print("-- UV Mapping Completed.")
        print()

        file.close()

        mesh = bpy.data.meshes.new(names[0])
        mesh.from_pydata(verts, [], faces)

        object = bpy.data.objects.new(names[0], mesh)

        bpy.context.collection.objects.link(object)


        print("-- Applying Smooth Shading to Mesh.")
        # Smooth out mesh
        mesh = object.data
        for f in mesh.polygons:
            f.use_smooth = True


        print("-- Assigning New Meterial to Mesh.")
        mat = bpy.data.materials.new(name=names[0])

        if object.data.materials:
            object.data.materials[0] = mat
        else:
            object.data.materials.append(mat)

        print("-- Attempting to understand MID data chunk, possible UV data...")
        print("-- Still in development.")
        #uv_layer = mesh.uv_layers.active.data
        #uv_layer = mesh.uv_layers.new(name=names[0])
        #for polpy in mesh.polygons:
            #print("Polygon index: %d, length: %d" % (polpy.index, polpy.loop_total))
            #for loop_index in range(polpy.loop_start, polpy.loop_start + polpy.loop_total):
                #print("    Vertex: %d" % mesh.loops[loop_index].vertex_index)
                # causes error ↓
                #print("    UV: %r" % uv_layer[loop_index].uv)

        print ("DONE")


#def extract_dds_png(filepath):
    #file = open(filepath, "rb")

    #file.seek(0x400)
    #names = file.read(256).decode("ascii").split(",\r\n")


def export_cat_file(filepath):
        print("~~~Foobar~~~~")

class ESM_MT_export_cat(Operator, ExportHelper):
        bl_idname = "export.cat"
        bl_label = "Export CAT"

        filename_ext = ".cat"

        def execute(self, operator):
                export_cat_file(self.properties.filepath)
                return { "FINISHED FOOBAR" }

class ESM_MT_import_cat(Operator, ImportHelper):
        bl_idname = "import.cat"
        bl_label = "Import CAT"

        filename_ext = ".cat"

        def execute(self, operator):
                import_cat_file(self.properties.filepath)
                return { "FINISHED" }

def menu_func(self, context):
        self.layout.operator(ESM_MT_import_cat.bl_idname, text = "Senran Kagura: Burst Renewal (*.cat)")
        # unimplemented
        #self.layout.operator(ESM_MT_export_cat.bl_idname, text = "Senran Kagura: Burst Renewal (*.cat)")
        # TEST

def register():
        bpy.utils.register_class(ESM_MT_import_cat)
        bpy.types.TOPBAR_MT_file_import.append(menu_func)
        # unimplemented
        #bpy.utils.register_class(ESM_MT_export_cat)
        #bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister():
        bpy.utils.unregister_class(ESM_MT_import_cat)
        bpy.types.TOPBAR_MT_file_import.remove(menu_func)
        # unimplemented
        #bpy.utils.unregister_class(ESM_MT_export_cat)
        #bpy.types.TOPBAR_MT_file_export.remove(menu_func)

if __name__ == "__main__":
        register()
