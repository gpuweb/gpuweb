/******************************************************************************
 *                 JS Extension for the W3C Spec Style Sheet                  *
 *                                                                            *
 * This code handles:                                                         *
 * - some fixup to improve the table of contents                              *
 * - the obsolete warning on outdated specs                                   *
 ******************************************************************************/
(function() {
  "use strict";
  var ESCAPEKEY = 27;
  var collapseSidebarText = '<span aria-hidden="true">←</span> '
                          + '<span>Collapse Sidebar</span>';
  var expandSidebarText   = '<span aria-hidden="true">→</span> '
                          + '<span>Pop Out Sidebar</span>';
  var tocJumpText         = '<span aria-hidden="true">↑</span> '
                          + '<span>Jump to Table of Contents</span>';

  var sidebarMedia = window.matchMedia('screen and (min-width: 78em)');
  var autoToggle   = function(e){ toggleSidebar(e.matches) };
  if(sidebarMedia.addListener) {
    sidebarMedia.addListener(autoToggle);
  }

  function toggleSidebar(on, skipScroll) {
    if (on == undefined) {
      on = !document.body.classList.contains('toc-sidebar');
    }

    if (!skipScroll) {
      /* Don't scroll to compensate for the ToC if we're above it already. */
      var headY = 0;
      var head = document.querySelector('.head');
      if (head) {
        // terrible approx of "top of ToC"
        headY += head.offsetTop + head.offsetHeight;
      }
      skipScroll = window.scrollY < headY;
    }

    var toggle = document.getElementById('toc-toggle');
    var tocNav = document.getElementById('toc');
    if (on) {
      var tocHeight = tocNav.offsetHeight;
      document.body.classList.add('toc-sidebar');
      document.body.classList.remove('toc-inline');
      toggle.innerHTML = collapseSidebarText;
      if (!skipScroll) {
        window.scrollBy(0, 0 - tocHeight);
      }
      tocNav.focus();
      sidebarMedia.addListener(autoToggle); // auto-collapse when out of room
    }
    else {
      document.body.classList.add('toc-inline');
      document.body.classList.remove('toc-sidebar');
      toggle.innerHTML = expandSidebarText;
      if (!skipScroll) {
        window.scrollBy(0, tocNav.offsetHeight);
      }
      if (toggle.matches(':hover')) {
        /* Unfocus button when not using keyboard navigation,
           because I don't know where else to send the focus. */
        toggle.blur();
      }
    }
  }

  function createSidebarToggle() {
    /* Create the sidebar toggle in JS; it shouldn't exist when JS is off. */
    var toggle = document.createElement('a');
      /* This should probably be a button, but appearance isn't standards-track.*/
    toggle.id = 'toc-toggle';
    toggle.class = 'toc-toggle';
    toggle.href = '#toc';
    toggle.innerHTML = collapseSidebarText;

    sidebarMedia.addListener(autoToggle);
    var toggler = function(e) {
      e.preventDefault();
      sidebarMedia.removeListener(autoToggle); // persist explicit off states
      toggleSidebar();
      return false;
    }
    toggle.addEventListener('click', toggler, false);


    /* Get <nav id=toc-nav>, or make it if we don't have one. */
    var tocNav = document.getElementById('toc-nav');
    if (!tocNav) {
      tocNav = document.createElement('p');
      tocNav.id = 'toc-nav';
      /* Prepend for better keyboard navigation */
      document.body.insertBefore(tocNav, document.body.firstChild);
    }
    /* While we're at it, make sure we have a Jump to Toc link. */
    var tocJump = document.getElementById('toc-jump');
    if (!tocJump) {
      tocJump = document.createElement('a');
      tocJump.id = 'toc-jump';
      tocJump.href = '#toc';
      tocJump.innerHTML = tocJumpText;
      tocNav.appendChild(tocJump);
    }

    tocNav.appendChild(toggle);
  }

  var toc = document.getElementById('toc');
  if (toc) {
    if (!document.getElementById('toc-toggle')) {
      createSidebarToggle();
    }
    toggleSidebar(sidebarMedia.matches, true);

    /* If the sidebar has been manually opened and is currently overlaying the text
       (window too small for the MQ to add the margin to body),
       then auto-close the sidebar once you click on something in there. */
    toc.addEventListener('click', function(e) {
      if(document.body.classList.contains('toc-sidebar') && !sidebarMedia.matches) {
        var el = e.target;
        while (el != toc) { // find closest <a>
          if (el.tagName.toLowerCase() == "a") {
            toggleSidebar(false);
            return;
          }
          el = el.parentElement;
        }
      }
    }, false);
  }
  else {
    console.warn("Can't find Table of Contents. Please use <nav id='toc'> around the ToC.");
  }

  /* Amendment Diff Toggling */
  var showDiff = function(event) {
    var a = event.target.parentElement.parentElement;
    var ins = document.querySelectorAll("ins[cite='#" + a.id + "'], #" + a.id + " ins" );
    var del = document.querySelectorAll("del[cite='#" + a.id + "'], #" + a.id + " del" );
    ins.forEach( function(e) { e.hidden = false; e.classList.remove("diff-inactive") });
    del.forEach( function(e) { e.hidden = false; e.classList.remove("diff-inactive") });
    a.querySelectorAll("button[value=diff]")[0].disabled = true;
    a.querySelectorAll("button[value=old]")[0].disabled = false;
    a.querySelectorAll("button[value=new]")[0].disabled = false;
  }
  var showOld = function(event) {
    var a = event.target.parentElement.parentElement;
    var ins = document.querySelectorAll("ins[cite='#" + a.id + "'], #" + a.id + " ins" );
    var del = document.querySelectorAll("del[cite='#" + a.id + "'], #" + a.id + " del" );
    ins.forEach( function(e) { e.hidden = true;  e.classList.add("diff-inactive") });
    del.forEach( function(e) { e.hidden = false; e.classList.add("diff-inactive") });
    a.querySelectorAll("button[value=diff]")[0].disabled = false;
    a.querySelectorAll("button[value=old]")[0].disabled = true;
    a.querySelectorAll("button[value=new]")[0].disabled = false;
  }
  var showNew = function(event) {
    var a = event.target.parentElement.parentElement;
    var ins = document.querySelectorAll("ins[cite='#" + a.id + "'], #" + a.id + " ins" );
    var del = document.querySelectorAll("del[cite='#" + a.id + "'], #" + a.id + " del" );
    ins.forEach( function(e) { e.hidden = false;  e.classList.add("diff-inactive") });
    del.forEach( function(e) { e.hidden = true; e.classList.add("diff-inactive") });
    a.querySelectorAll("button[value=diff]")[0].disabled = false;
    a.querySelectorAll("button[value=old]")[0].disabled = false;
    a.querySelectorAll("button[value=new]")[0].disabled = true;
  }
  var amendments = document.querySelectorAll('[id].amendment, [id].correction, [id].addition');
  amendments.forEach( function(a) {
    var ins = document.querySelectorAll("ins[cite='#" + a.id + "'], #" + a.id + " ins" );
    var del = document.querySelectorAll("del[cite='#" + a.id + "'], #" + a.id + " del" );
    if (ins.length == 0 && del.length == 0) { return; }

    var tbar = document.createElement('div');
    tbar.lang = 'en'; tbar.class = 'amendment-toggles';

    var toggle = document.createElement('button');
    toggle.value = 'diff'; toggle.innerHTML = 'Show Change'; toggle.disabled = true;
    toggle.addEventListener('click', showDiff, false);
    tbar.appendChild(toggle);

    toggle = document.createElement('button');
    toggle.value = 'old'; toggle.innerHTML = 'Show Current';
    toggle.addEventListener('click', showOld, false);
    tbar.appendChild(toggle);

    toggle = document.createElement('button');
    toggle.value = 'new'; toggle.innerHTML = 'Show Future';
    toggle.addEventListener('click', showNew, false);
    tbar.appendChild(toggle);

    a.appendChild(tbar);
  });

  /* Wrap tables in case they overflow */
  var tables = document.querySelectorAll(':not(.overlarge) > table.data, :not(.overlarge) > table.index');
  var numTables = tables.length;
  for (var i = 0; i < numTables; i++) {
    var table = tables[i];
    if (!table.matches('.example *, .note *, .advisement *, .def *, .issue *')) {
      /* Overflowing colored boxes looks terrible, and also
         the kinds of tables inside these boxes
         are less likely to need extra space. */
      var wrapper = document.createElement('div');
      wrapper.className = 'overlarge';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  }

  /* Deprecation warning */
  if (document.location.hostname === "www.w3.org" && /^\/TR\/\d{4}\//.test(document.location.pathname)) {
    var request = new XMLHttpRequest();

    request.open('GET', 'https://www.w3.org/TR/tr-outdated-spec');
    request.onload = function() {
      if (request.status < 200 || request.status >= 400) {
        return;
      }
      try {
        var currentSpec = JSON.parse(request.responseText);
      } catch (err) {
        console.error(err);
        return;
      }
      document.body.classList.add("outdated-spec");
      var node = document.createElement("p");
      node.classList.add("outdated-warning");
      node.tabIndex = -1;
      node.setAttribute("role", "dialog");
      node.setAttribute("aria-modal", "true");
      node.setAttribute("aria-labelledby", "outdatedWarning");
      if (currentSpec.style) {
          node.classList.add(currentSpec.style);
      }

      var frag = document.createDocumentFragment();
      var heading = document.createElement("strong");
      heading.id = "outdatedWarning";
      heading.innerHTML = currentSpec.header;
      frag.appendChild(heading);

      var anchor = document.createElement("a");
      anchor.href = currentSpec.latestUrl;
      anchor.innerText = currentSpec.latestUrl + ".";

      var warning = document.createElement("span");
      warning.innerText = currentSpec.warning;
      warning.appendChild(anchor);
      frag.appendChild(warning);

      var button = document.createElement("button");
      var handler = makeClickHandler(node);
      button.addEventListener("click", handler);
      button.innerHTML = "&#9662; collapse";
      frag.appendChild(button);
      node.appendChild(frag);

      function makeClickHandler(node) {
        var isOpen = true;
        return function collapseWarning(event) {
          var button = event.target;
          isOpen = !isOpen;
          node.classList.toggle("outdated-collapsed");
          document.body.classList.toggle("outdated-spec");
          button.innerText = (isOpen) ? '\u25BE collapse' : '\u25B4 expand';
        }
      }

      document.body.appendChild(node);
      button.focus();
      window.onkeydown = function (event) {
        var isCollapsed = node.classList.contains("outdated-collapsed");
        if (event.keyCode === ESCAPEKEY && !isCollapsed) {
          button.click();
        }
      }

      window.addEventListener("click", function(event) {
        if (!node.contains(event.target) && !node.classList.contains("outdated-collapsed")) {
          button.click();
        }
      });

      document.addEventListener("focus", function(event) {
        var isCollapsed = node.classList.contains("outdated-collapsed");
        var containsTarget = node.contains(event.target);
        if (!isCollapsed && !containsTarget) {
          event.stopPropagation();
          node.focus();
        }
      }, true); // use capture to enable event delegation as focus doesn't bubble up
    };

    request.onerror = function() {
      console.error("Request to https://www.w3.org/TR/tr-outdated-spec failed.");
    };

    request.send();
  }

  /* Dark mode toggle */
  const darkCss = document.querySelector('link[href^="https://www.w3.org/StyleSheets/TR/2016/dark"]');
  if (darkCss) {
    const colorScheme = localStorage.getItem("tr-theme") || "auto";
    darkCss.disabled = colorScheme === "light";
    darkCss.media = colorScheme === "auto" ? "(prefers-color-scheme: dark)" : "";
    const render = document.createElement("div");
    function createOption(option) {
      const checked = option === colorScheme;
      return `
        <label>
          <input name="color-scheme" type="radio" value="${option}" ${checked ? "checked": ""}>
          <span>${option}</span>
        </label>
      `.trim();
    }
    render.innerHTML = `
      <a id="toc-theme-toggle" role="radiogroup" aria-label="Select a color scheme">
        <span aria-hidden="true"><img src="https://www.w3.org/StyleSheets/TR/2016/logos/dark.svg" title="theme toggle icon" /></span>
        <span>
        ${["light", "dark", "auto"].map(createOption).join("")}
        </span>
      </a>
    `;
    const changeListener = (event) => {
      const { value } = event.target;
      darkCss.disabled = value === "light";
      darkCss.media = value === "auto" ? "(prefers-color-scheme: dark)" : "";
      localStorage.setItem("tr-theme", value);
    };
    render.querySelectorAll("input[type='radio']").forEach((input) => {
      input.addEventListener("change", changeListener);
    });

    var tocNav = document.querySelector('#toc-nav');
    tocNav.appendChild(...render.children);
  }


  /* Matomo analytics */
  if (document.location.hostname === "www.w3.org" && /^\/TR\//.test(document.location.pathname)) {
    var _paq = window._paq = window._paq || [];
    /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    (function() {
      var u="https://www.w3.org/analytics/piwik/";
      _paq.push(['setTrackerUrl', u+'matomo.php']);
      _paq.push(['setSiteId', '447']);
      var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
      g.type='text/javascript'; g.async=true; g.src=u+'matomo.js'; s.parentNode.insertBefore(g,s);
    })();
  }

})();
