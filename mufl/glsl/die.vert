#version 330

uniform mat4 proj;
uniform mat4 rot;
uniform vec2 pos;

in vec2 in_vert;
in vec4 in_color;
in vec3 in_norm;
in ivec2 in_uv;
out vec2 uv;
out vec4 color;
out float norm_z;
uniform sampler2D tex;

void main() {
    gl_Position = proj * (vec4(pos, 0.0, 0.0) + rot * vec4(in_vert * 20, 0.0, 1.0));
    uv = vec2(in_uv) / textureSize(tex, 0);
    color = in_color;
    norm_z = (proj * rot * vec4(in_norm, 0.0)).z;
}
