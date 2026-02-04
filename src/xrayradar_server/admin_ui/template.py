"""HTML template for admin UI."""

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>xrayradar admin</title>
    <style>
      __CSS__
    </style>
  </head>
  <body>
    <header>
      <div>
        <div class="title">xrayradar admin</div>
        <div class="meta">Logged in as <span id="who">__EMAIL__</span></div>
      </div>
      <div class="row" style="max-width: 320px">
        <button id="refresh" class="small">Refresh</button>
        <button id="logout" class="small danger">Logout</button>
      </div>
    </header>

    <div class="layout">
      <aside>
        <div class="sideInner">
          <div class="navItem" data-view="tokens" role="link" tabindex="0">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Tokens</div>
              <div class="muted" style="margin-top: 2px">Create and manage access</div>
            </div>
          </div>
          <div class="navItem" data-view="requests" role="link" tabindex="0" style="margin-top: 8px">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Token requests</div>
              <div class="muted" style="margin-top: 2px">Fulfill user requests</div>
            </div>
          </div>
          <div class="navItem" data-view="users" role="link" tabindex="0" style="margin-top: 8px">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Users</div>
              <div class="muted" style="margin-top: 2px">Manage plans</div>
            </div>
          </div>
          <div class="navItem" data-view="deletions" role="link" tabindex="0" style="margin-top: 8px">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Deletions</div>
              <div class="muted" style="margin-top: 2px">Account deletion requests</div>
            </div>
          </div>
          <div class="navItem" data-view="logs" role="link" tabindex="0" style="margin-top: 8px">
            <span class="navDot" aria-hidden="true"></span>
            <div>
              <div style="font-weight: 700; font-size: 13px">Project logs</div>
              <div class="muted" style="margin-top: 2px">Browse stored events</div>
            </div>
          </div>
        </div>
      </aside>

      <div class="content">
        <div id="view_tokens" class="view">
          <div class="grid2">
            <section>
              <h2>Create token</h2>
              <div class="muted">Create a token tied to an email/name. Grant project access from the right panel.</div>

              <label>Name</label>
              <input id="t_name" placeholder="app-ingest" />

              <label>Email (optional)</label>
              <input id="t_email" placeholder="owner@example.com" />

              <label>Admin</label>
              <select id="t_admin">
                <option value="false" selected>False</option>
                <option value="true">True</option>
              </select>

              <div style="margin-top: 12px" class="row">
                <button id="create" class="primary">Create</button>
              </div>

              <div id="create_out" class="ok" style="margin-top: 10px"></div>
              <div id="create_err" class="error" style="margin-top: 10px"></div>

              <hr style="border: 0; border-top: 1px solid #1f2937; margin: 14px 0" />

              <h2>Tokens</h2>
              <div class="muted">Click a token to manage its project access.</div>
              <div style="margin-top: 10px; overflow-x: auto; max-width: 100%;">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Flags</th>
                    </tr>
                  </thead>
                  <tbody id="tokens"></tbody>
                </table>
              </div>
            </section>

            <section>
              <div class="toolbar">
                <div>
                  <h2 style="margin-bottom: 4px">Token access</h2>
                  <div class="muted">Selected token: <span id="selected">(none)</span></div>
                </div>
                <button id="revoke_token" class="small danger" disabled>Revoke token</button>
              </div>

              <div id="access_err" class="error" style="margin: 8px 0"></div>

              <div class="row" style="align-items: flex-end">
                <div>
                  <label>Project</label>
                  <select id="projects"></select>
                </div>
                <div>
                  <button id="grant" class="primary" disabled>Grant</button>
                </div>
              </div>

              <div style="margin-top: 12px">
                <table>
                  <thead>
                    <tr>
                      <th>Access ID</th>
                      <th>Project ID</th>
                      <th>Created</th>
                      <th>Revoked</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody id="grants"></tbody>
                </table>
              </div>
            </section>
          </div>
        </div>

        <div id="view_requests" class="view hidden">
          <section>
            <h2>Token requests</h2>
            <div class="muted">Users can request a token. Fulfill a request to create a token linked to that user.</div>

            <div id="req_err" class="error" style="margin-top: 10px"></div>
            <div id="req_out" class="ok" style="margin-top: 10px"></div>

            <div style="margin-top: 12px">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>User</th>
                    <th>Name</th>
                    <th>Created</th>
                    <th>Fulfilled</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody id="req_rows"></tbody>
              </table>
            </div>
          </section>
        </div>

        <div id="view_users" class="view hidden">
          <section>
            <h2>Users</h2>
            <div class="muted">View and manage user plans. Change a user's plan to Free, Basic, or Pro.</div>

            <div id="users_err" class="error" style="margin-top: 10px"></div>
            <div id="users_out" class="ok" style="margin-top: 10px"></div>

            <div style="margin-top: 12px">
              <table>
                <thead>
                  <tr>
                    <th style="width: 50px">ID</th>
                    <th style="width: 30%">Email</th>
                    <th style="width: 100px">Plan</th>
                    <th style="width: 100px">Events</th>
                    <th style="width: 140px">Created</th>
                    <th style="width: 180px">Change Plan</th>
                  </tr>
                </thead>
                <tbody id="users_rows"></tbody>
              </table>
            </div>
          </section>
        </div>

        <div id="view_deletions" class="view hidden">
          <section>
            <h2>Account Deletion Requests</h2>
            <div class="muted">Review and fulfill user account deletion requests. Fulfilling a request permanently deletes the user and all their data.</div>

            <div id="del_err" class="error" style="margin-top: 10px"></div>
            <div id="del_out" class="ok" style="margin-top: 10px"></div>

            <div style="margin-top: 12px">
              <table>
                <thead>
                  <tr>
                    <th style="width: 50px">ID</th>
                    <th style="width: 30%">User Email</th>
                    <th style="width: 30%">Reason</th>
                    <th style="width: 140px">Requested</th>
                    <th style="width: 120px"></th>
                  </tr>
                </thead>
                <tbody id="del_rows"></tbody>
              </table>
            </div>
          </section>
        </div>

        <div id="view_logs" class="view hidden">
          <section>
            <h2>Project logs</h2>
            <div class="muted">Browse raw stored events per project, with lightweight filtering and event payload viewing.</div>

            <div class="row" style="margin-top: 12px; align-items: flex-end">
              <div style="flex: 0.8; min-width: 140px">
                <label>Project</label>
                <select id="logs_project"></select>
              </div>
              <div style="flex: 0.8; min-width: 140px">
                <label>Level</label>
                <select id="logs_level">
                  <option value="" selected>(any)</option>
                  <option value="error">error</option>
                  <option value="warning">warning</option>
                  <option value="info">info</option>
                  <option value="debug">debug</option>
                </select>
              </div>
              <div style="flex: 0.8; min-width: 140px">
                <label>Environment</label>
                <input id="logs_env" placeholder="production" />
              </div>
              <div style="flex: 0.8; min-width: 140px">
                <label>Release</label>
                <input id="logs_release" placeholder="1.2.3" />
              </div>
            </div>

            <div class="row" style="margin-top: 10px; align-items: flex-end">
              <div style="flex: 2">
                <label>Search message</label>
                <input id="logs_q" placeholder="contains..." />
              </div>
              <div style="flex: 0.8">
                <button id="logs_load" class="primary">Load</button>
              </div>
              <div style="flex: 0.8">
                <button id="logs_more" disabled>Load more</button>
              </div>
            </div>

            <div id="logs_err" class="error" style="margin-top: 10px"></div>
          </section>

          <section style="margin-top: 16px">
            <div class="muted" style="margin-bottom: 10px">Tip: click a row to view full JSON payload.</div>
            <table>
              <thead>
                <tr>
                  <th style="width: 180px">Time</th>
                  <th style="width: 90px">Level</th>
                  <th style="width: 160px">Environment</th>
                  <th style="width: 160px">Release</th>
                  <th>Message</th>
                </tr>
              </thead>
              <tbody id="logs_rows"></tbody>
            </table>
          </section>

          <div id="logs_modal" class="modalOverlay hidden" role="dialog" aria-modal="true" aria-label="Event detail">
            <div class="modalCard" style="background: #0f172a; border: 1px solid #1f2937; border-radius: 12px">
              <div class="modalHeader">
                <div style="min-width: 0">
                  <div class="modalTitle">Event detail</div>
                  <div class="muted" style="margin-top: 4px">
                    <span id="logs_modal_meta" class="mono"></span>
                  </div>
                </div>
                <div style="display: flex; gap: 8px; align-items: center">
                  <button id="logs_copy" class="small">Copy JSON</button>
                  <button id="logs_modal_close" class="modalClose small">×</button>
                </div>
              </div>
              <div class="modalBody">
                <div id="logs_modal_msg" class="ok" style="margin-bottom: 10px"></div>
                <pre id="logs_payload" class="codeblock mono"></pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      __JS__
    </script>
  </body>
</html>"""
