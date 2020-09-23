#version 330

uniform mat4 proj;
uniform mat4 rot;
uniform vec3 pos;
uniform float size;

in vec3 in_vert;
in ivec2 in_uv;
out vec2 uv;
uniform sampler2D tex;

void main() {
    gl_Position = proj * (vec4(pos, 0.0) + rot * vec4(in_vert * size, 1.0));
    uv = vec2(in_uv) / textureSize(tex, 0);
}
