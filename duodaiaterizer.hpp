// duodaiaterizer.hpp
#pragma once
#include "vector.hpp"

namespace TGDK {

class Duodaiaterizer {
public:
    static Vector3f Contract(const Vector3f& v, float Q) {
        // Opposite of Duoquadratlizer expansion
        return v / (Q * Q);
    }

    static Vector3f Balance(const Vector3f& v, float Q, bool expand) {
        if (expand) {
            return v * (Q * Q);   // Duoquadratlizer
        } else {
            return v / (Q * Q);   // Duodaiaterizer
        }
    }
};

}