/* ============================================================
   TIME FADES PHOTOBOOTH - script.js
   Vanilla JS. Mobile nav, contact form (Formspree), small polish.
   ============================================================ */
(function () {
  "use strict";

  /* ---- Mobile nav toggle ---- */
  var toggle = document.getElementById("navToggle");
  var menu = document.getElementById("navMenu");

  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    });

    // Close the menu after tapping a link (mobile)
    menu.addEventListener("click", function (e) {
      if (e.target.tagName === "A" && menu.classList.contains("is-open")) {
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
      }
    });
  }

  /* ---- Footer year ---- */
  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  /* ---- Contact / booking form (Formspree) ----
     Submits via fetch so the visitor stays on the page. Must stay in sync with
     the action="" on the <form> in index.html, which is the no-JS fallback.
  */
  var FORMSPREE_ENDPOINT = "https://formspree.io/f/xnjeoqgo";

  var form = document.getElementById("quoteForm");
  var status = document.getElementById("formStatus");

  if (form && status) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      // Simple client-side check (name + valid email required)
      if (!form.checkValidity()) {
        setStatus("Please add your name and a valid email so we can reach you.", "err");
        form.reportValidity();
        return;
      }

      var submitBtn = form.querySelector('button[type="submit"]');
      var originalLabel = submitBtn ? submitBtn.textContent : "";
      if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = "Sending…"; }
      setStatus("Sending…", "");

      fetch(FORMSPREE_ENDPOINT, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" }
      })
        .then(function (res) {
          if (res.ok) {
            form.reset();
            setStatus("Thank you. We've got your note and will be in touch soon.", "ok");
          } else {
            // Formspree returns JSON errors; surface a friendly message
            setStatus("Something went wrong sending that. Please try again, or call us directly.", "err");
          }
        })
        .catch(function () {
          // Network failure (offline, blocked request) - never leave the visitor
          // guessing; point them at the phone/email in the sidebar instead.
          setStatus("We couldn't send that just now. Please try again, or reach us by phone or email.", "err");
        })
        .finally(function () {
          if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = originalLabel; }
        });
    });
  }

  function setStatus(msg, kind) {
    if (!status) return;
    status.textContent = msg;
    status.classList.remove("is-ok", "is-err");
    if (kind === "ok") status.classList.add("is-ok");
    if (kind === "err") status.classList.add("is-err");
  }

  /* ---- Gallery lightbox ----
     Click (or Enter/Space) a gallery tile to view it full-size, with
     prev/next + keyboard nav. Handles both photo tiles and the film
     tile: if a tile ever holds a <video>, the lightbox plays that;
     otherwise it shows the image. So when Jim's real clip is dropped
     into the film tile, this needs no changes.
  */
  var galleryItems = Array.prototype.slice.call(
    document.querySelectorAll(".gallery__item")
  );

  if (galleryItems.length) {
    var currentIndex = 0;
    var lastFocused = null;

    // Build the overlay once, in JS, so it only exists when JS is on
    // and index.html stays uncluttered.
    var box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "Photo viewer");
    box.innerHTML =
      '<button type="button" class="lightbox__close" aria-label="Close viewer">&times;</button>' +
      '<button type="button" class="lightbox__nav lightbox__prev" aria-label="Previous photo">&#8249;</button>' +
      '<figure class="lightbox__stage">' +
      '<div class="lightbox__media"></div>' +
      '<figcaption class="lightbox__caption"></figcaption>' +
      "</figure>" +
      '<button type="button" class="lightbox__nav lightbox__next" aria-label="Next photo">&#8250;</button>';
    document.body.appendChild(box);

    var mediaEl = box.querySelector(".lightbox__media");
    var captionEl = box.querySelector(".lightbox__caption");
    var closeBtn = box.querySelector(".lightbox__close");
    var prevBtn = box.querySelector(".lightbox__prev");
    var nextBtn = box.querySelector(".lightbox__next");

    // Make each tile keyboard-operable and announce what it opens.
    galleryItems.forEach(function (item, i) {
      var cap = item.querySelector("figcaption");
      var label = cap ? "View photo: " + cap.textContent.trim() : "View photo";
      item.setAttribute("role", "button");
      item.setAttribute("tabindex", "0");
      item.setAttribute("aria-label", label);
      item.addEventListener("click", function () { open(i); });
      item.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " " || e.key === "Spacebar") {
          e.preventDefault();
          open(i);
        }
      });
    });

    function render(index) {
      var item = galleryItems[index];
      var cap = item.querySelector("figcaption");
      var video = item.querySelector("video");
      mediaEl.innerHTML = "";

      if (video) {
        // Clone the tile's video so it plays in the viewer.
        var v = video.cloneNode(true);
        v.setAttribute("controls", "");
        v.removeAttribute("width");
        v.removeAttribute("height");
        v.className = "lightbox__img";
        mediaEl.appendChild(v);
      } else {
        var src = item.querySelector("img");
        var big = document.createElement("img");
        big.className = "lightbox__img";
        big.src = src ? (src.currentSrc || src.src) : "";
        big.alt = src ? src.alt : "";
        mediaEl.appendChild(big);
      }
      captionEl.textContent = cap ? cap.textContent.trim() : "";
    }

    function open(index) {
      currentIndex = index;
      lastFocused = document.activeElement;
      render(index);
      box.classList.add("is-open");
      document.body.classList.add("has-lightbox");
      closeBtn.focus();
      document.addEventListener("keydown", onKey);
    }

    function close() {
      box.classList.remove("is-open");
      document.body.classList.remove("has-lightbox");
      document.removeEventListener("keydown", onKey);
      stopMedia();
      if (lastFocused && lastFocused.focus) lastFocused.focus();
    }

    function stopMedia() {
      var v = mediaEl.querySelector("video");
      if (v) { try { v.pause(); } catch (err) {} }
    }

    function step(dir) {
      stopMedia();
      currentIndex = (currentIndex + dir + galleryItems.length) % galleryItems.length;
      render(currentIndex);
    }

    function onKey(e) {
      if (e.key === "Escape") { close(); }
      else if (e.key === "ArrowLeft") { step(-1); }
      else if (e.key === "ArrowRight") { step(1); }
      else if (e.key === "Tab") { trapFocus(e); }
    }

    // Keep focus inside the dialog while it's open.
    function trapFocus(e) {
      var focusable = [closeBtn, prevBtn, nextBtn];
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
      }
    }

    closeBtn.addEventListener("click", close);
    prevBtn.addEventListener("click", function () { step(-1); });
    nextBtn.addEventListener("click", function () { step(1); });
    // Click the dark backdrop (but not the photo or a control) to close.
    box.addEventListener("click", function (e) {
      if (e.target === box || e.target === mediaEl || e.target.classList.contains("lightbox__stage")) {
        close();
      }
    });
  }
})();
