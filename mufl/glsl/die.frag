#version 330

out vec4 f_color;
in vec2 uv;
in float norm_z;
uniform sampler2D tex;
uniform vec3 color;

void main() {
    f_color = vec4(texture(tex, uv).rgb * color, 1.0);
}
