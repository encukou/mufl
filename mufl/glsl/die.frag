#version 330

out vec4 f_color;
in vec2 uv;
in vec4 color;
uniform sampler2D tex;

void main() {
    f_color = color * vec4(1.0, 1.0, 1.0, 1.0) * 0.5 + texture(tex, uv) * 0.5;
}
